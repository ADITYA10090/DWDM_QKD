from flask import Flask, request, render_template_string, redirect, url_for
from flask_socketio import SocketIO, join_room, emit, disconnect
import json
from least_candidate_from_csv import (
    get_least_S_for_Q_excluding_CCh_from_csv,
    load_exclusion_list,
    save_exclusion_list
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Fixed sets (do not change these by default)
Q_demo = (1530, 1537, 1538)
# Exclusion list is loaded from file on demand.

# Global dictionaries for pairing and chat room management.
pending_pairs = {}             # pair (tuple) -> True (pending request exists)
pair_to_channel = {}           # pair (tuple) -> assigned quantum channel (as int)
allowed_pair_for_channel = {}  # channel (int) -> allowed pair (tuple)
chat_logs = {}                 # channel (int) -> list of chat messages

# Global dictionary to count how many queries have been submitted for each pair.
pair_query_count = {}          # pair (tuple) -> int

# Dictionary to keep track of connection counts per channel.
room_counts = {}
# Map client socket id to the channel they joined.
client_room = {}

def process_request(a, b):
    """
    Process classical identifiers A and B.
    The pair is created by sorting (so (1,2) and (2,1) are the same).
    Increment the query count for the pair.
    If the query count exceeds 2, this means two valid queries already exist
    and any additional query is rejected.
    
    If this is the first query, mark the pair as pending and return (None, waiting_room).
    If a complementary query already exists (and query count is exactly 2),
    load the exclusion list, perform the CSV lookup to assign a quantum channel,
    update the exclusion list, store the allowed pair, and return (channel, waiting_room).
    """
    try:
        a_int = int(a)
        b_int = int(b)
    except ValueError:
        return None, None

    pair = tuple(sorted((a_int, b_int)))
    waiting_room = f"waiting_{pair[0]}-{pair[1]}"

    # Increment the query count.
    pair_query_count[pair] = pair_query_count.get(pair, 0) + 1

    # If more than two queries for this pair, reject it.
    if pair_query_count[pair] > 2:
        return None, None

    # If a channel was already assigned for this pair, return it.
    if pair in pair_to_channel:
        return pair_to_channel[pair], waiting_room

    # If this is the second (complementary) query:
    if pair in pending_pairs:
        current_exclusion = load_exclusion_list()
        result = get_least_S_for_Q_excluding_CCh_from_csv(Q_demo, current_exclusion, filename="results.csv")
        if result:
            gi, S = result
            gi = int(gi)  # ensure native int
            pair_to_channel[pair] = gi
            allowed_pair_for_channel[gi] = pair
            current_exclusion.append(gi)
            save_exclusion_list(current_exclusion)
            # Initialize chat log for this channel.
            chat_logs[gi] = []
            del pending_pairs[pair]
            # Notify waiting clients that the channel has been assigned.
            socketio.emit("channel_assigned", {"channel": gi}, room=waiting_room)
            return gi, waiting_room
        else:
            return None, waiting_room
    else:
        # First query: mark the pair as pending.
        pending_pairs[pair] = True
        return None, waiting_room

# Waiting page template.
waiting_template = """
<!doctype html>
<html>
<head>
    <title>Waiting for Quantum Channel</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.1/socket.io.min.js"
            crossorigin="anonymous" referrerpolicy="no-referrer"></script>
</head>
<body>
    <h2>Quantum Channel Request</h2>
    {% if error %}
      <p style="color:red;">{{ error }}</p>
    {% endif %}
    <form method="post" action="{{ url_for('index') }}">
        <label for="a">Your Identifier (A):</label>
        <input type="text" id="a" name="a" required>
        <br>
        <label for="b">Other Identifier (B):</label>
        <input type="text" id="b" name="b" required>
        <br>
        <button type="submit">Send Request</button>
    </form>
    {% if waiting_room %}
        <h3>Waiting for complementary request...</h3>
        <p>Your request is registered. Please wait until the other party submits their complementary request.</p>
        <div id="status"></div>
        <script>
            var socket = io();
            socket.emit('join_waiting', {'room': '{{ waiting_room }}'});
            socket.on('channel_assigned', function(data) {
                // When channel is assigned, check its current connection count.
                fetch("/channel_status?channel=" + data.channel)
                  .then(response => response.json())
                  .then(json => {
                      if (json.count < 2) {
                          // If channel is not full, redirect to chat.
                          window.location.href = "/chat?channel=" + data.channel;
                      } else {
                          // Otherwise, redirect back to the query page.
                          document.getElementById('status').textContent = "Channel is full. Redirecting to query page...";
                          setTimeout(function(){ window.location.href = "/"; }, 3000);
                      }
                  })
                  .catch(err => {
                      document.getElementById('status').textContent = "Error checking channel status.";
                  });
            });
        </script>
    {% endif %}
</body>
</html>
"""

# Chat page template.
chat_template = """
<!doctype html>
<html>
<head>
    <title>Quantum Channel Chat</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.1/socket.io.min.js"
            crossorigin="anonymous" referrerpolicy="no-referrer"></script>
</head>
<body>
    <h2>Quantum Channel Chat</h2>
    <p>You have been assigned quantum channel: <strong>{{ channel }}</strong></p>
    <div id="chat">
        <ul id="messages" style="list-style-type: none; padding: 0;"></ul>
        <input id="message_input" autocomplete="off" placeholder="Type a message..." style="width:300px;">
        <button id="send_button">Send</button>
        <button id="end_button">End</button>
    </div>
    <script>
        var socket = io();
        socket.emit('join', {'channel': {{ channel }}});
        socket.emit('request_history', {'channel': {{ channel }}});
        socket.on('chat_history', function(data) {
            var messages = document.getElementById('messages');
            messages.innerHTML = "";
            data.history.forEach(function(msg) {
                var item = document.createElement('li');
                item.textContent = msg;
                messages.appendChild(item);
            });
        });
        socket.on('chat_message', function(data) {
            var messages = document.getElementById('messages');
            var item = document.createElement('li');
            item.textContent = data.msg;
            messages.appendChild(item);
        });
        document.getElementById('send_button').onclick = function() {
            var input = document.getElementById('message_input');
            var message = input.value.trim();
            if (message) {
                socket.emit('send_message', {'channel': {{ channel }}, 'msg': message});
                input.value = '';
            }
        };
        document.getElementById('end_button').onclick = () => {
            socket.emit('end', {'channel': {{ channel }}});
        }
        socket.on('redirect', function(data) {
            window.location.href = data.url;
        });
    </script>
</body>
</html>
"""

# New endpoint to check channel connection count.
@app.route('/channel_status')
def channel_status():
    channel = request.args.get('channel')
    try:
        channel = int(channel)
    except:
        return {"error": "invalid channel"}
    count = room_counts.get(channel, 0)
    return {"count": count}

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        a = request.form.get('a')
        b = request.form.get('b')
        channel, waiting_room = process_request(a, b)
        if channel:
            # Valid pair complete; redirect to chat.
            return redirect(url_for('chat', channel=channel))
        else:
            # If process_request returned None without a waiting_room,
            # it means the pair has already submitted 2 queries.
            if waiting_room is None:
                error = "Channel for that pair is already full. Please try different identifiers."
            return render_template_string(waiting_template, waiting_room=waiting_room, error=error)
    return render_template_string(waiting_template, waiting_room=None, error=error)

@app.route('/waiting')
def waiting():
    room = request.args.get('room')
    return render_template_string(waiting_template, waiting_room=room, error=None)

@app.route('/return')
def returnHome():
    return render_template_string(waiting_template,waiting_room=None,error=None)

@app.route('/chat')
def chat():
    channel = request.args.get('channel')
    if channel:
        return render_template_string(chat_template, channel=channel)
    else:
        return redirect(url_for('index'))

@socketio.on('join')
def on_join(data):
    channel = int(data['channel'])
    # Restrict connections: only allow if fewer than 2 users are in the room.
    if room_counts.get(channel, 0) >= 2:
        emit('chat_message', {'msg': 'Error: This channel is full.'})
        disconnect()
        return
    join_room(channel)
    room_counts[channel] = room_counts.get(channel, 0) + 1
    client_room[request.sid] = channel
    # Send chat history to this client.
    if channel in chat_logs:
        emit('chat_history', {'history': chat_logs[channel]})
    emit('chat_message', {'msg': f'A new user has joined quantum channel {channel}.'}, room=channel)

@socketio.on('join_waiting')
def on_join_waiting(data):
    room = data['room']
    join_room(room)

@socketio.on('send_message')
def handle_message(data):
    channel = int(data['channel'])
    msg = data['msg']
    if channel in chat_logs:
        chat_logs[channel].append(msg)
    else:
        chat_logs[channel] = [msg]
    emit('chat_message', {'msg': msg}, room=channel)

@socketio.on('request_history')
def handle_history(data):
    channel = int(data['channel'])
    history = chat_logs.get(channel, [])
    emit('chat_history', {'history': history})

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in client_room:
        channel = client_room[sid]
        room_counts[channel] = room_counts.get(channel, 1) - 1
        if room_counts[channel] < 0:
            room_counts[channel] = 0
        del client_room[sid]

@socketio.on('end')
def on_end(data):
    sid = request.sid
    try:
        channel = client_room[request.sid]
        for i in client_room:
            print(client_room[i], channel)
            if(client_room[i]==channel):
                socketio.emit('redirect', {'url': '/return'}, room=i)
        remove_number_from_json(channel)
    except KeyError:
        print("error getting room no")
    print("click registered on end button",client_room)

def remove_number_from_json(ch):
    try:
        # Read the JSON file
        with open("exclusion_list.json", 'r') as file:
            data = json.load(file)

        # Remove occurrences of the number
        updated_data = [num for num in data if num != ch]

        print(len(data), len(updated_data))

        # Write back to the JSON file
        with open("exclusion_list.json", 'w') as file:
            json.dump(updated_data, file, indent=4)

        print(f"Number {ch} removed successfully.")
    except Exception as e:
        print(f"Error: {e}")

def clear_json():
    try:
        with open("exclusion_list.json",'w') as file:
            json.dump("",file,)
    except Exception as e:
        print(f"except -> {e}")
    

if __name__ == '__main__':
    # clear_json()
    socketio.run(app, debug=True)