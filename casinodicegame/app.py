from gevent import monkey
monkey.patch_all()

from flask import Flask, redirect, request, url_for, session
from flask.ext.socketio import SocketIO, emit, join_room
from casinodicegame.game import Game
import uuid

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

games = {}


@app.route('/')
def root():
    game_id = uuid.uuid1()
    game_url = url_for('game', game_id=game_id)
    games[game_url] = Game()
    return redirect(url_for('game', game_id=game_id))


@app.route('/games/<game_id>')
def game(game_id):
    print games.keys()
    return app.send_static_file('index.html')


@socketio.on('start')
def start(message):
    room = session['room']
    game = games[room]
    game.start_game()
    update(game, room)


@socketio.on('join')
def join(message):
    room = message['room']
    join_room(room)
    session['room'] = room
    player_id = session['user_id']
    game = games[room]
    game.join(player_id)
    update(game, room)
    request.namespace.emit('userId', session['user_id'])


@socketio.on('play')
def play(action):
    room = session['room']
    game = games[room]
    if game.current_player.player_id != session['user_id']:
        return
    for _ in game.play(int(action)):
        update(game, room)


@socketio.on('restart')
def restart(message):
    room = session['room']
    game = games[room]
    game.reset()
    update(game, room)


@app.before_request
def get_or_set_user_id():
    user_id = session.get('user_id')
    if user_id is None:
        user_id = str(uuid.uuid1())
        session['user_id'] = user_id


def update(game, room):
    emit('update', game.serialize(), room=room)


if __name__ == '__main__':
    socketio.run(app, use_reloader=False)
