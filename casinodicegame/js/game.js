/** @jsx React.DOM */
(function () {
  'use strict';

  var React = require('react');
  var ReactDOM = require('react-dom');
  window.React = React;
  window.ReactDOM = ReactDOM;

  var winners_by_casino = {};
  var current_player = {color: 'blue', rolled_dice: {}};
  var userId = null;
  var diceRollMP3 = null;

  var GameView = React.createClass({
    getInitialState: function() {
      return {rolledDice: {}, players: [], 'dice_per_casino': [],
              'casino_bills': [], 'winners_by_casino': [],
              'last_played_dice': []};
    },
    render: function () {
      var players = [];
      var casinos = [];
      var actions = [];
      for (var i=0; i<this.state.players.length; i++) {
        players.push(<Player key={'player' + i}
                             player={this.state.players[i]}
                             currentPlayer={this.state.current_player}/>);
      }
      for (var number=1; number < 7; number++) {
        var diceToPlay = this.state.current_player ? this.state.current_player.rolled_dice[number] : {};
        casinos.push(
          <Casino key={number}
                  currentPlayer={this.state.current_player}
                  diceToPlay={diceToPlay}
                  number={number}
                  dice={this.state.dice_per_casino[number]}
                  bills={this.state.casino_bills[number]}
                  winners={this.state.winners_by_casino[number] || []}
                  playedDice={this.state.last_played_dice[number] || {}}/>);
        }
        if (this.state.state == 'join') {
          actions.push(<button key='join' className="action"
                               onClick={start}>Start</button>);
        } else if (this.state.state == 'gameover') {
          actions.push(<button key='gameover' className="action"
                               onClick={restart}>Reset</button>);
        }
        return <div className="game">
                 <div className="players" key='players'>{players}</div>
                 {actions}
                 {casinos}
               </div>;
      }
    });

    var Casino = React.createClass({
      render: function () {
        if (!this.props.bills) return <div className="casino"></div>;
        var toPlay = [];
        var i = -1;
        var self = this;
        var components = this.props.bills.map(function (bill) {
          i++;
          return <div key={i}
                      className={"bill bill-" + bill + " winner-" +
                                 self.props.winners[i]} >{bill}
                 </div>;
        });
        for (i=0; i < this.props.dice.length; i++) {
          var dice = this.props.dice[i];
          components.push(<Dice key={i + 'die'}
                               color={dice[0]}
                               number={dice[1]}
                               playedDice={this.props.playedDice[dice[0]]}/>);
        }
        if (this.props.diceToPlay &&
            (this.props.diceToPlay[0] || this.props.diceToPlay[1])) {
          toPlay = <div className="to-play">
                     <button onClick={play.bind(this, this.props.number)}>
                       <Dice color={this.props.currentPlayer.color}
                            number={this.props.diceToPlay[0]}/>
                       <Dice color="white" number={this.props.diceToPlay[1]}/>
                     </button>
                   </div>;
        } else {
          toPlay = <div className="to-play"></div>;
        }
        return <div className="casino">{toPlay}{components}</div>;
      }
    });

    var Die = React.createClass({
      defaultProps: {
        lastPlayedBy: '',
      },
      render: function () {
        return <div className={'die ' + this.props.color +
                               (this.props.lastPlayedBy ? ' last-played ' : '') +
                                ' last-played-' + this.props.lastPlayedBy}></div>;
      }
    });

    var Dice = React.createClass({
      render: function () {
        var components = [];
        for (var i=0; i < this.props.number; i++) {
          var lastPlayedBy =  this.props.playedDice ? this.props.playedDice[i] : '';
          components.push(<Die key={'die' + i} color={this.props.color} lastPlayedBy={lastPlayedBy}/>);
        }
        return <div className="dice-group">{components}</div>;
      }
    });

    var Player = React.createClass({
      render: function () {
        return <div className={"player " + this.props.player.color + " " + (this.props.currentPlayer ? (this.props.player.color == this.props.currentPlayer.color ? "current-player" : "") : "")}>
                 <span className="score">{this.props.player.score}</span>
                 <Die color={this.props.player.color}/> {this.props.player.dice}<br/>
                 <Die color="white"/> {this.props.player.white_dice}
               </div>;
      }
    });

    var gameView = ReactDOM.render(
      <GameView/>,
      document.getElementById('game')
    );

    var io = require('socket.io-client');
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('connect', function() {
      socket.emit('join', {room: window.location.pathname});
    });

    socket.on('update', function (message) {
      window.incoming = JSON.parse(message);
      if (window.incoming.current_player && userId == window.incoming.current_player.player_id) {
        if (diceRollMP3) {
          diceRollMP3.pause();
          diceRollMP3.currentTime = 0;
          diceRollMP3.play();
        }
        document.body.style.backgroundColor = 'lightblue';
      } else {
        document.body.style.backgroundColor = 'white';
      }
      gameView.setState(window.incoming);
    });

    socket.on('userId', function (newUserId) {
      userId = newUserId;
    });

    socket.on('alert', function (message) {
      alert(message);
    });

    function play(casino) {
      socket.emit('play', casino);
    }

    function start() {
      diceRollMP3 = new Audio('/static/dice.mp3');
      socket.emit('start', '');
    }

    function restart() {
      socket.emit('restart', '');
    }

    window.socket = socket;
  })();
