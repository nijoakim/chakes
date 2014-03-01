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

////////////////////////////////////////////////////////////////
// Example usage
////////////////////////////////////////////////////////////////

class ExampleServer(port: Int) extends Server(port) {
	
	def onMessage(netMsg: NetworkMessage, user: User): Unit = {
		netMsg match {
			case netMsg: Message => {
				for (userR <- users) {
					userR.oStream.writeObject(Message(user.name +": "+ netMsg.str))
					userR.oStream.flush
				}
			}
		}
	}
}

object ServerMain extends App {
	println("Server")
	
	val server = new ExampleServer(4444)
	//server.close
}

////////////////////////////////////////////////////////////////
// Server class
////////////////////////////////////////////////////////////////

abstract class Server(port: Int) {
	val users = new mutable.ArrayBuffer[User] with mutable.SynchronizedBuffer[User]
	private val serverSocket = new ServerSocket(port)
	
	private var kill = false
	
	actor {
		while (!kill) {
			val socket = serverSocket.accept
			val oStream = new ObjectOutputStream(new BufferedOutputStream(socket.getOutputStream)); oStream.flush
			val iStream = new ObjectInputStream(new BufferedInputStream(socket.getInputStream))
			actor {
				// TODO: Time out
				iStream.readObject match {
					case str: String => {
						val newUser = User(socket, str, iStream, oStream)
						users += newUser
						newUserPollActor(newUser)
					}
					case obj => throwUnexpectedObjectException(obj)
				}
			}
			
			Thread.sleep(100)
		}
	}
	
	private def newUserPollActor(user: User): Unit = actor {
		while (true) {
			user.iStream.readObject  match {
				case netMsg: NetworkMessage => {
					onMessage(netMsg, user)
				}
				case obj => throwUnexpectedObjectException(obj)
			}
			Thread.sleep(100)
		}
	}
	
	private def throwUnexpectedObjectException(obj: Object): Unit = {
		throw new ChakesNetworkException("Unexptected object sent over network: '"+ obj.getClass +"'.")
	}
	
	def close: Unit =  kill = true
	def onMessage(netMsg: NetworkMessage, user: User): Unit
	
}
