/* Copyright 2016 Kim Albertsson
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
'use strict'

module.exports = (function () {

	function isString(s) {
    	return typeof(s) === 'string' || s instanceof String;
	}

	var API = {from: {
		engine   : {to: { webserver: {
			newGame: {
				new: function (id, rule) {
					return {msgName:'newGame', id: id, rule: rule};
				},
				verify: function (msg) {
					if ( ! msg.hasOwnProperty('id') && 
						   msg.hasOwnProperty('rule') ) {
						// Validate properties
						return false;
					}

					if ( ! Number.isSafeInteger(msg.id) &&
					       isString(msg.rule) ) {
						// Validate types
						return false;
					}
					
					// Passes all validation
					return true;
				}
			},
			updateAt: {
				new: function (id, dst, piece) {
					return {msgName:'updateAt', id: id, dst: {x:dst.x, y:dst.y}, piece: piece};
				},
				verify: function (msg) {
					if (msg.msgName != "updateAt") { return false; }
					if ( ! msg.hasOwnProperty('id') && msg.hasOwnProperty('dst') ) {
						// Validate properties
						return false;
					}

					if ( ! Number.isSafeInteger(msg.id) && 
						   msg.dst instanceof Object ) {
						// Validate types
						return false;
					}

					if (! msg.dst.hasOwnProperty('x')     && 
						  Number.isSafeInteger(msg.dst.x) &&
						  msg.dst.hasOwnProperty('y')     && 
						  Number.isSafeInteger(msg.dst.y) ) {
						// Additional tests for nested object dst
						return false;
					}

					// All gates passed, message validated
					return true;
				},
			},
		}}},
		webserver: {to: {
			engine   : {
				newGame     : function (rule) {
					return {msgName:'newGame', rule: rule};
				},
				addPlayer   : function (id, player) {
					return {msgName:'addPlayer', id: id, player: player};
				},
				startGame   : function (id) {
					return {msgName:'startGame', id: id};
				},
				applyAction : function (id, name, player, src, dst) {
					return {msgName:'applyAction', id: id, name: name, player: player, src: src, dst: dst};
				},
			},
			webclient: {

			},
		}},
		webclient: {to: { webserver: {

		}}}
	}}

	return API;
})();