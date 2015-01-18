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

import scala.actors.Actor.actor
import scala.collection._

// =============
// Example usage
// =============

object ClientMain extends App {
	println("Client")
	
	val client = new Client("localhost", 4444, readLine)
}

// ============
// Client class
// ============

class Client(host: String, port: Int, userName: String) {
	val socket = new Socket(host, port)
	val iStream = new ObjectInputStream(new BufferedInputStream(socket.getInputStream))
	val oStream = new ObjectOutputStream(new BufferedOutputStream(socket.getOutputStream))
	oStream.flush
	
	actor {
		while (true) {
			iStream.readObject match {
				case msg: Message => println(msg.str)
			}
		}
	}
	
	oStream.writeObject(userName)
	
	while (true) {
		val str = readLine
		oStream.writeObject(Message(str))
		oStream.flush
	}
}
