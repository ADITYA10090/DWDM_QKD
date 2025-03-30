from flask import Flask, request, render_template_string, redirect, url_for, jsonify
from flask_socketio import SocketIO, join_room, emit, disconnect
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
allowed_pair_for_channel = {}  # channel (int) -> pair (tuple) allowed in the room
chat_logs = {}                 # channel (int) -> list of chat messages

# Dictionary to keep track of connection counts per channel.
room_counts = {}
# Map client socket id to the channel they joined.
client_room = {}

def process_request(a, b):
    """
    Process classical identifiers A and B.
    The pair is created by sorting (so (1,2) and (2,1) are the same).
    If this is the first request, mark the pair as pending and return (None, waiting_room).
    If the complementary request exists, load the exclusion list,
    perform the CSV lookup to assign a quantum channel, update the exclusion list,
    store the allowed pair, and return (channel, waiting_room).
    """
    try:
        a_int = int(a)
        b_int = int(b)
    except ValueError:
        return None, None

    pair = tuple(sorted((a_int, b_int)))
    waiting_room = f"waiting_{pair[0]}-{pair[1]}"

    if pair in pair_to_channel:
        return pair_to_channel[pair], waiting_room

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
        pending_pairs[pair] = True
        return None, waiting_room

# New endpoint to check channel connection count.
@app.route('/channel_status')
def channel_status():
    channel = request.args.get('channel')
    try:
        channel = int(channel)
    except:
        return jsonify({"error": "invalid channel"})
    count = room_counts.get(channel, 0)
    return jsonify({"count": count})

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
                          // Redirect only if channel is not full.
                          window.location.href = "/chat?channel=" + data.channel;
                      } else {
                          // Otherwise, redirect back to the main query page.
                          document.getElementById('status').textContent = "Channel is full. Please submit your request again.";
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
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        a = request.form.get('a')
        b = request.form.get('b')
        channel, waiting_room = process_request(a, b)
        if channel:
            return redirect(url_for('chat', channel=channel))
        else:
            return redirect(url_for('waiting', room=waiting_room))
    return render_template_string(waiting_template, waiting_room=None)

@app.route('/waiting')
def waiting():
    room = request.args.get('room')
    return render_template_string(waiting_template, waiting_room=room)

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

if __name__ == '__main__':
    socketio.run(app, debug=True)
