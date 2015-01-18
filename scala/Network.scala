/* Copyright 2014 Joakim Nilsson
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

package chakes.network

import java.net._
import java.io._

////////////////////////////////////////////////////////////////
// Chakes network exception
////////////////////////////////////////////////////////////////

case class ChakesNetworkException(msg: String) extends Exception(msg)

////////////////////////////////////////////////////////////////
// Misc. classes
////////////////////////////////////////////////////////////////

case class User(socket: Socket, name: String, iStream: ObjectInputStream, oStream: ObjectOutputStream)
class NetworkMessage()
case class Message(str: String) extends NetworkMessage
