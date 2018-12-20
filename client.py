import socket
import threading
import wltp
import time

HOST = '127.0.0.1'
PORT = 65432
username = None
groupid = None
playing = False
score = 0

def GetInput():
	request_type = input()
	json_data = None
	if request_type == "create":
		json_data = None

	elif request_type == "delete":
		json_data = None

	elif request_type == "join":
		print("groupid(-1代表随机):",end="")
		groupid = input()
		json_data = {"groupid":int(groupid)}

	elif request_type == "leave":
		json_data = None

	elif request_type == "submit":
		print("answer:",end="")
		answer = input()
		json_data = {"answer":answer}

	elif request_type == "register":
		print("username:",end="")
		username = input()
		json_data = {"username":username}

	elif request_type == "start":
		print("contest_times:",end="")
		contest_times = input()
		json_data = {"contest_times":contest_times}

	elif request_type == "end":
		json_data = None

	return request_type,json_data

def RECV(sock):
	global username
	global score
	while True:
		try:
			recv_data = sock.recv(1024).decode()
			recv_data = wltp.response(data=recv_data)
			if recv_data.status != "200 OK":
				print(recv_data.status)
			else:
				if recv_data.json_data["result"]!="success":
					print(recv_data.json_data["result"])

				if recv_data.json_data["result"] == "success":

					if recv_data.response_type == "register":
						username = recv_data.json_data["username"]
						print("success")

					elif recv_data.response_type == "create":
						print("success")
						print("your groupid:"+str(recv_data.json_data["groupid"]))


					elif recv_data.response_type == "delete":
						print("your group has been deleted")
						groupid = None
						pass

					elif recv_data.response_type == "join":
						if recv_data.json_data["username"] == username:
							groupid = recv_data.json_data["groupid"]
						print(recv_data.json_data["username"]+" join group " + str(recv_data.json_data["groupid"]))

					elif recv_data.response_type == "leave":
						if recv_data.json_data["username"] == username:
							groupid = None
						print(recv_data.json_data["username"]+" leave group " + str(recv_data.json_data["groupid"]))
							
					elif recv_data.response_type == "start":
						playing = True
						score = 0
						print("The contest have "+str(recv_data.json_data["contest_times"]) +" times,the first time will start in 3 seconds.")
						for i in range(3):
							print(i)
							time.sleep(1)

					elif recv_data.response_type == "end":
						playing = False
						print("The contest is over.")

					elif recv_data.response_type == "submit":
						if recv_data.json_data["username"] == username:
							score += recv_data.json_data["score"]
						if int(recv_data.json_data["score"])>0:
							print(recv_data.json_data["username"]+"'s answer is correct.Get "+recv_data.json_data["score"] +" points")
						else:
							print(recv_data.json_data["username"]+"'s answer is wrong")

					elif recv_data.response_type == 'message':   ###question指令
						print(recv_data.json_data["message"])
			# print('Received',repr(recv_data))
			# if recv_data == b'exit':
			# 	break
		except ConnectionResetError:
			print("服务器已经挂掉1。。")
			break

if __name__ == '__main__':

	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
	
	try:
		sock.connect((HOST,PORT))

		thread = threading.Thread(target = RECV,args = (sock,))
		thread.start()

		while True:
			request_type,json_data = GetInput()
			try:
				sock.sendall(( wltp.request(url=HOST,request_type=request_type,json_data = json_data).getall() ).encode())
				# if send_data == b'exit':
				# 	thread.join()
				# 	break
			except ConnectionResetError:
				print("服务器已经挂掉2。。")
				
	except ConnectionRefusedError:
		print("无法连接到服务器")

	sock.close()		

