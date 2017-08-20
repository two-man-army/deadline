class WebSocketConnection:
    def __init__(self, socket, owner_id, opponent_id):
        self.web_socket = socket
        self.owner_id = owner_id
        self.opponent_id = opponent_id
        self.is_valid = False

    def __hash__(self):
        return hash(str(self.owner_id) + str(self.opponent_id))

    def __eq__(self, other):
        return self.owner_id == other.owner_id and self.opponent_id == other.opponent_id
