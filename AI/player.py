from asyncio.windows_events import NULL
import random
from queue import Queue
from numpy import zeros, array, roll, vectorize

_ADD = lambda a, b: (a[0] + b[0], a[1] + b[1])
_HEX_STEPS = array([(1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1)], 
    dtype="i,i")
_CAPTURE_PATTERNS = [[_ADD(n1, n2), n1, n2] 
    for n1, n2 in 
        list(zip(_HEX_STEPS, roll(_HEX_STEPS, 1))) + 
        list(zip(_HEX_STEPS, roll(_HEX_STEPS, 2)))]
_SWAP_PLAYER = { 0: 0, 1: 2, 2: 1 }

class Player:


    def __init__(self, player, n):
        """
        Called once at the beginning of a game to initialise this player.
        Set up an internal representation of the game state.

        The parameter player is the string "red" if your player will
        play as Red, or the string "blue" if your player will play
        as Blue.
        """
        # put your code here
        if player == "red":
            self.player = 1
        else:
            self.player = 2
        self.n = n
        self.board = zeros((n, n), dtype=int)
        self.count = 1
        self.redfirst = (-1, -1)
        self.dest = []
        for i in range(2):
            self.dest.append([])
        self.currentHex = None
        self.state = 0
        self.allytokens = []
        self.connectedline = []
        self.lineNum = 0
        self.fillEmpty = []
        if self.player == 1:
            for i in range(n):
                self.dest[1].append((n-1, i))
                self.dest[0].append((0, i))
        else:
            for i in range(n):
                self.dest[0].append((i, 0))
                self.dest[1].append((i, n-1))


    def action(self):
        """
        Called at the beginning of your turn. Based on the current state
        of the game, select an action to play.
        """
        # put your code here
        
        if self.count == 1:
            
            if self.player == 1:
            #1 for red 2 for blue
                if self.n % 2 == 0:
                    q = int(self.n/2 - 2)
                else:
                    q = int((self.n+1)/2 - 2)
                self.count += 1
                self.currentHex = (q, q)
                self.startHex = (q, q)
                self.board[self.currentHex] = 1
                self.defState()         
                self.allytokens.append(self.currentHex)    
                return ("PLACE", q, q)

            else:
                if self.n % 2 == 0:
                    cd = int(self.n/2)
                    coord = [(cd, cd), (cd+1, cd), (cd, cd+1), (cd+1, cd+1)]
                    for i in coord:
                        if self.board[i[0]][i[1]] == 1:
                            self.count += 1
                            self.board[i[1]][i[0]] = 2
                            self.currentHex = (i[1], i[0])
                            self.startHex = (i[1], i[0])
                            self.board[i[0]][i[1]] = 0
                            self.allytokens.append(self.currentHex)
                            self.defState()
                            return ("STEAL",)
                        else:
                            self.board[cd][cd] = 2
                            self.startHex = (cd, cd)
                            self.count += 1
                            self.currentHex = (cd, cd)
                            self.allytokens.append(self.currentHex)
                            self.defState()
                            return("PLACE", cd, cd)

                else:
                    coord = self.coord_neighbours((int((self.n+1)/2 - 1), int((self.n+1)/2 - 1)))
                    for i in coord:
                        if self.board[i[0]][i[1]] == 1:
                            self.count += 1
                            self.board[i[1]][i[0]] = 2
                            self.board[i[0]][i[1]] = 0
                            self.currentHex = (i[1], i[0])
                            self.startHex = (i[1], i[0])
                            self.allytokens.append(self.currentHex)
                            self.defState()
                            return ("STEAL",)
                        
                    self.count += 1
                    self.board[int((self.n+1)/2 - 1)][int((self.n+1)/2 - 1)] = 2
                    self.currentHex = (int((self.n+1)/2 - 1), int((self.n+1)/2 - 1))
                    self.startHex = (int((self.n+1)/2 - 1), int((self.n+1)/2 - 1))
                    self.allytokens.append(self.currentHex)
                    self.defState()
                    return ("PLACE", int((self.n+1)/2 - 1), int((self.n+1)/2 - 1))

        else:
            MAX = -1
            best_path = None
            coord = self.coord_neighbours(self.currentHex)
            if len(self.fillEmpty) > 0:
                if self.board[self.fillEmpty[0]] == 0:
                    self.board[self.fillEmpty[0]] = self.player
                    #print(self.fillEmpty)
                    fill_Empty = self.fillEmpty.pop(0)
                    self.allytokens.append(fill_Empty)
                    return ("PLACE", int(fill_Empty[0]), int(fill_Empty[1]))
            
            for c in coord:
                if self.board[c] == 0:
                    if c in self.dest[self.state]:
                        self.reverseState()
                        self.currentHex = self.startHex
                        self.board[c[0]][c[1]] = self.player
                        self.count += 1
                        self.allytokens.append(self.currentHex)
                        return ("PLACE", int(c[0]), int(c[1]))
                    for token in self.allytokens:
                        opp_coord = self.check_capture(token)
                        if opp_coord != None:
                            self.board[opp_coord] = self.player
                            self.count += 1
                            self.allytokens.append(opp_coord)
                            return ("PLACE", int(opp_coord[0]), int(opp_coord[1]))
                    if self.board[c[0], c[1]] == 0:
                        curr = self.EVAL((c[0], c[1]))
                        if curr > MAX:
                            MAX = curr
                            best_path = c
            self.currentHex = best_path
            self.allytokens.append(self.currentHex)
            self.count += 1
            self.board[best_path] = self.player
            return ("PLACE", int(best_path[0]), int(best_path[1]))
            



    def reverseState(self):
        if self.state == 0:
            self.state = 1
        else:
            self.state = 0                    

    def EVAL(self, coord):
    #state0 stand for going down for red and going left for blue
    #state1 stand for going up for red and going right for blue
        cap_coord = self._apply_captures(coord)
        if cap_coord != None:
            add_EVAL = 2
        else:
            add_EVAL = 0
        if self.player == 1:
            if self.state == 1:
                return (self.n - (self.n - coord[0])) + add_EVAL
            else:
                return self.n - coord[0] + add_EVAL

        else:
            if self.state == 0:
                return (self.n - coord[1]) + add_EVAL
            else:
                return self.n - (self.n - coord[1]) + add_EVAL    
    

    def turn(self, player, action):
        """
        Called at the end of each player's turn to inform this player of 
        their chosen action. Update your internal representation of the 
        game state based on this. The parameter action is the chosen 
        action itself. 
        
        Note: At the end of your player's turn, the action parameter is
        the same as what your player returned from the action method
        above. However, the referee has validated it at this point.
        """
        # put your code here
        if player == "red":
            ply = 1
        else:
            ply = 2
        if action[0] == "PLACE":
            if self.count == 2 and ply == 1:
                self.redfirst = (action[1], action[2])
            self.board[action[1]][action[2]] = ply
            coordi = (action[1], action[2])
            cap_coord = self._apply_captures(coordi)
            if ply != self.player:
                if cap_coord != None:
                    for cpc in cap_coord:
                        self.allytokens.remove(cpc)
                        self.fillEmpty.append(cpc)
        else:
            self.board[self.redfirst] = 0
            self.board[self.redfirst[1]][self.redfirst[0]] = 2


    def _apply_captures(self, coord):
        """
        Check coord for diamond captures, and apply these to the board
        if they exist. Returns a list of captured token coordinates.
        """
        opp_type = self.board[coord]
        mid_type = _SWAP_PLAYER[opp_type]
        captured = set()

        # Check each capture pattern intersecting with coord
        for pattern in _CAPTURE_PATTERNS:
            coords = [_ADD(coord, s) for s in pattern]
            # No point checking if any coord is outside the board!
            if all(map(self.inside_bounds, coords)):
                tokens = [self.board[cd[0]][cd[1]] for cd in coords]
                if tokens == [opp_type, mid_type, mid_type]:
                    # Capturing has to be deferred in case of overlaps
                    # Both mid cell tokens should be captured
                    captured.update(coords[1:])

        for coordi in captured:
            self.board[coordi] = 0

        return list(captured)

    def check_capture(self, coord):

        opp_type = self.board[coord]
        mid_type = _SWAP_PLAYER[opp_type]

        for pattern in _CAPTURE_PATTERNS:
            coords = [_ADD(coord, s) for s in pattern]
            # No point checking if any coord is outside the board!
            if all(map(self.inside_bounds, coords)):
                tokens = [self.board[cd[0]][cd[1]] for cd in coords]
                if tokens == [0, mid_type, mid_type]:
                    opp_coord = coords[0]
                    return opp_coord

        return None

    def place(self, token, coord):
        """
        Place a token on the board and apply captures if they exist.
        Return coordinates of captured tokens.
        """
        self[coord] = token
        return self._apply_captures(coord)


    def coord_neighbours(self, coord):
        """
        Returns (within-bounds) neighbouring coordinates for given coord.
        """
        return [_ADD(coord, step) for step in _HEX_STEPS \
            if self.inside_bounds(_ADD(coord, step))]

    def inside_bounds(self, coord):
        """
        True iff coord inside board bounds.
        """
        r, q = coord
        return r >= 0 and r < self.n and q >= 0 and q < self.n


    def defState(self):
        if self.player == 1:
            if self.currentHex[0] <= self.n/2:
                self.state = 1
            else:
                self.state = 0
        else:
            if self.currentHex[1] <= self.n/2:
                self.state = 0
            else:
                self.state = 1

    def connected_coords(self, start_coord):
        """
        Find connected coordinates from start_coord. This uses the token 
        value of the start_coord cell to determine which other cells are
        connected (e.g., all will be the same value).
        """
        # Get search token type
        token_type = self.board[start_coord]

        # Use bfs from start coordinate
        reachable = set()
        queue = Queue(0)
        queue.put(start_coord)

        while not queue.empty():
            curr_coord = queue.get()
            reachable.add(curr_coord)
            for coord in self.coord_neighbours(curr_coord):
                if coord not in reachable and self.board[coord] == token_type:
                    queue.put(coord)

        return list(reachable)

    def getConnected_coords(self):
        i = 0
        while i < len(self.allytokens): 
            connectedcd = self.connected_coords(self.allytokens[i])
            if connectedcd == self.allytokens and self.lineNum == 0:
                return None
            else:
                for ccd in connectedcd:
                    self.connectedline.append([])
                    self.connectedline[self.lineNum].append(ccd)
                    self.allytokens.remove(ccd)
                self.lineNum += 1

        
        
                
