# NetSym - The Open Source Network Simulation #

The program that enables users to create, connect and operate computers, 
routers, switches, hubs, servers and clients with a simple yet highly-functional user 
interface. Users can watch the packets get sent back and fourth with a **very** slowed 
down version of real life network protocols.

## Using the Program ##
When the program is started, no objects are drawn to screen.
There is a user interface interactive side-window that contains the buttons and actions
the user can perform.
By each button there is a key-combination in the keyboard that enables the same
action using the keyboard. It is naturally much faster.
When computers are drawn to the screen, they each have a randomly generated unique name.
Objects can be dragged around the screen with the mouse.
Once some object is selected, the information about it will be displayed in the `VIEW_MODE` 
on the side-window. Actions regarding that object will also be there.
The program can be paused by pressing the space bar.

Users can connect the computers to each other on the screen using the `connect computers` button
then pressing the first computer and then the second. It is also possible to press the 
connection between the computers to view details about it.
IP addresses can be given manually (using the computer's `set IP address` button) or
using a DHCP server that is connected to the same LAN as your computers. (Routers are 
DHCP servers by default)

## How It Works ##

#### Graphics Objects and the Main Loop ###

The program is based on using what's called `GraphicsObject`s which are objects that
each represent one object that is drawn repeatedly to the screen (for example computers,
packets, connections, buttons, etc...)
For each of those there is also an actual object that handles the logic, and the `GraphicsObject`\
handles the graphics and drawing only.
For example sending and wrapping an _ICMP_ packet will be in `Computer` while deciding
what processes will be drawn to the screen near a server computer will be in `ComputerGraphics`.

There is a main loop to the program. It is in `main_loop.py` file. The main loop draws
all of the `GraphicsObject`s, moves all of the packets and runs all of the main functions of
the other objects, for example the main function of the `Computer` class is the `logic` method
which handles all of sending and receiving packets. It is called in the main loop method.  

Each `GraphicsObject` has a `draw` and `move` methods. Respectively, one handles drawing the actual graphics
while the other handles other movements that should happen repeatedly.
Upon Creation, a `GraphicsObject` inserts these two methods to the main loop to be called
on every loop of the program.

When a `GraphicsObject` has `GraphicsObject` attributes recursively needs to put them inside a `child_graphics_objects`
iterable in-order for them to be unregistered when the main object is unregistered.

When a packet is sent, it leaves the `Interface` object of the sending computer,
It goes into the `sent_packets` list of the `Connection` it is sent through.
The connection constantly updates the location of the `PacketGraphics` according to its
time in the connection. 
When the packet reached its destination it is moved to the `Interface` object of the 
receiving computer and picked up by its `logic` method to be handled in the different processes.

#### Computer Connections and Interfaces ####
When Connecting two computers, The first interfaces of their interface-lists that is not connected will be 
connected to each other.
If there is no such interface for one of the computers, it will be created.
Computers can also be connected directly from their interfaces (drawn like little 
squares next to the computers themselves).
Each computer starts with a loopback interface. Packets that are sent on it are drawn going in circle
from the computer back to it.

#### Processes ####
Each computer can run several processes at the same.
Processes need usually to wait for some packet for a large period of time and it cannot just block
the main loop, so processes are actually _generator_ functions that yield the packet type they are waiting for.
The `Computer` class actually implements a sort of scheduler that knows when and how long to run each process.  

### Thank You For Using NetSym!!! ###

* Fin
* Fin Ack
* Ack