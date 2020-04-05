from socket import * 
import sys
import re
import time
import pickle
import _thread as thread


user_timeline = []
subs = []
activeUsers = []
endSessionLock = thread.allocate_lock()
global endSession
endSession = False
######################################
#          Driver Method             #
# connects to server, starts client  #
# thread, and gets user input        #
######################################
def main():
    global endSession
    host, port, user = validateArgs(sys.argv)
    csock = connect(host, port, user)
    thread.start_new_thread(listening, (csock,))
    activeUsers.append(user)
    while True:
        endSessionLock.acquire()
        if endSession:
            endSessionLock.release()
            sys.exit()
        endSessionLock.release()
        option = input("\nOptions: tweet, subscribe, unsubscribe, timeline, getusers, gettweets, exit: ").split()
        performAction(option, user, csock)
        time.sleep(.25)
        
###########################################
# Client Thread handling server responses #
###########################################
def listening(conn):
    global endSession
    while True:
        try:
            data = conn.recv(1024).decode().split()
            # print("here1")
        except:
            d = conn.recv(2048)
            data = pickle.loads(d)
            print("here2")
            print(data)
        if data[0] == "rep":
            user_timeline.append(str(data[1]) + ": " + str(data[2]) + " " +str(data[3]))
            print(str(data[1]) + ": " + str(data[2]) + " " +str(data[3]))
        if data[0] == "good":
            print("operation success")
        if data[0] == "tooMany":
            print("sub <hashtag> failed, already exists or exceeds 3 limitation")
        if data[0] == "user":
            for user in data[1:]:
                print(user)
        if data[0] == "tweets":
            ###part of Justin's gettweets
            # for tweet in tweets[1:]:
            #     print(tweet)
            thisTweet = ""
            for tweet in data[1:]:
                thisTweet += tweet + " " 
            print(thisTweet)

        if data[0] == "ended":
            print("bye bye")
            endSessionLock.acquire()
            endSession = True
            endSessionLock.release()
            conn.close()
            thread.exit()
        ###part of Justin's getusers
        # if data[0] == "user":
        #     for user in data[1:]:
        #         print(user)
        if data[0] == "incoming":
            for person in data[1:]:
                print(person)
        if data[0] == "notIn":
            print("no user <Username> in the system")
            
#########################
# Handles User Requests #
#########################
def performAction(option, user, csock): 
    if (len(option) == 2 and option[0] == "subscribe" and validateTag(option[1])):
        subscribe(user, option[1], csock)
    if (len(option) >= 3 and option[0] == "tweet"): 
        tag = str(option.pop())
        message = option[1]
        valid = True
        if (len(message) >= 150):
            valid = False
            print("message length illegal, connection refused.")
        if valid: 
            tweet(message, tag, user, csock) 
    elif "tweet" == option[0]:
        print("message format illegal.")
    if len(option) == 2 and option[0] == "unsubscribe":
        unsubscribe(user, option[1], csock)
    if (len(option) == 1 and option[0] == "timeline"):
        timeline()
    if len(option) == 1 and option[0] == "getusers": 
        getUsers(user, csock)
    if len(option) == 2 and option[0] == "gettweets":
        getTweets(user, option[1], csock)
    if len(option) == 1 and option[0] == "exit":
        exit(user, csock)

###############################################
# Helpers for sending user requests to server #
###############################################
def tweet(message, tag, user, conn):
    code = "tweet " + str(message) + " " + str(tag) + " " + str(user)
    conn.sendall(code.encode())

def subscribe(user, tag, conn): 
    if len(subs) > 3: #parameter checking
        print("sub <hashtag> failed, already exists or exceeds 3 limitation") #error code
    else:
        subs.append(tag)
        code = "sub " + str(user) + " " + str(tag) #send to server
        conn.sendall(code.encode())

def unsubscribe(user, tag, conn):
    if tag not in subs: 
        return None
    subs.remove(tag)
    code = "unsub " + str(user) + " " + str(tag)
    conn.sendall(code.encode())

def getUsers(user, conn):
    code = "users " + str(user)
    conn.sendall(code.encode())

def getTweets(user, username, conn):
    code = "getTweets " + str(user) + " " + str(username)
    conn.sendall(code.encode())

def timeline():
    for tweet in user_timeline:
       print(tweet)

def exit(user, conn):
    code = "exit " + str(user)
    conn.sendall(code.encode())

###################################
# Helper for Connecting to server #
###################################
def connect(host, port, user): 
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((host, port))
    except:
        print("error: server ip invalid, connection refused.")
        sock = None
        sys.exit()
    sock.sendall(user.encode())
    loggedIn = sock.recv(1024).decode()
    if loggedIn == 'True': 
        print('username legal, connection established')
        return sock
    else: 
        print('username illegal, connection refused')
        sys.exit()

############################
# Input Validation Helpers #
############################
# Validates user arguments
def validateArgs(args):
    ### Regular Expression for IPv4 validation 
    regexIP = '''^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
            25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
            25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
            25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)'''
    ### Regular expression username constrants 
    regexUser = "^[a-zA-Z0-9_]*$"
    if len(args) != 4: 
        print('error: args should contain <ServerIP> <Server Port> <Username>')
        sys.exit()
    host, port, user = args[1], int(args[2]), args[3]
    if port < 1024 or port > 65535: 
        print('error: server port invalid, connection refused')
        sys.exit()
    if not re.search(regexIP, host):
       print('error: server ip invalid, connection refused') 
       sys.exit()
    if not re.search(regexUser, user):
        print('error: username has wrong format, connection refused')
        
    return host, port, user

# Helper for hashtag validation 
def validateTag(tag):
    valid = True
    for index in range(len(tag)-1):
        if tag[index] == tag[index+1]:
            if tag[index] == "#":
                valid = False
                print('hashtag illegal format, connection refused.')
    return valid

main()