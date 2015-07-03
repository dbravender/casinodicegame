/** @jsx React.DOM */
(function () {
  'use strict';

  var React = require('react');
  window.React = React;

  var casino_bills = {
    1: [],
    2: [],
    3: [],
    4: [],
    5: [],
    6: []
  };

  var dice_per_casino = {
    1: [],
    2: [],
    3: [],
    4: [],
    5: [],
    6: []
  };

  var winners_by_casino = {};
  var current_player = {color: 'blue', rolled_dice: {}};

  var GameView = React.createClass({
    getInitialState: function() {
      return {rolledDice: {}};
    },
    render: function () {
      var components = [];
      for (var number=1; number < 7; number++) {
        var diceToPlay = this.props.current_player ? this.props.current_player.rolled_dice[number] : {};
        components.push(
          <Casino key={number}
                  currentPlayer={this.props.current_player}
                  diceToPlay={diceToPlay}
                  number={number}
                  dice={this.props.dice_per_casino[number]}
                  bills={this.props.casino_bills[number]}
                  winners={this.props.winners_by_casino[number] || []}/>);
        }
        return <div className="casinos">{components}</div>;
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
          var die = this.props.dice[i];
          components.push(<Die key={i + 'die'} color={die[0]} number={die[1]}/>);
        }
        if (this.props.diceToPlay &&
            (this.props.diceToPlay[0] || this.props.diceToPlay[1])) {
          toPlay = <div className="to-play">
                     <button onClick={play.bind(this, this.props.number)}>
                       <Die color={this.props.currentPlayer.color}
                            number={this.props.diceToPlay[0]}/>
                       <Die color="white" number={this.props.diceToPlay[1]}/>
                     </button>
                   </div>;
        } else {
          toPlay = <div className="to-play"></div>;
        }
        return <div className="casino">{toPlay}{components}</div>;
      }
    });

    var Die = React.createClass({
      render: function () {
        var components = [];
        for (var i=0; i < this.props.number; i++) {
          components.push(<div key={'die' + i}
                               className={"die " + this.props.color}>
                          </div>);
        }
        return <div className="dice-group">{components}</div>;
      }
    });

    var gameView = React.render(
      <GameView casino_bills={casino_bills}
                dice_per_casino={dice_per_casino}
                current_player={current_player}
                winners_by_casino={winners_by_casino}/>,
      document.getElementById('game')
    );

    var io = require('socket.io-client');
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('connect', function() {
      socket.emit('join', {room: window.location.pathname});
    });

    socket.on('update', function (message) {
      window.incoming = JSON.parse(message);
      gameView.setProps(JSON.parse(message));
    });

    socket.on('alert', function (message) {
      alert(message);
    });

    function play(casino) {
      socket.emit('play', casino);
    }

    window.socket = socket;
  })();
