import socket
import threading
import queue
import random
import wltp
import time

GROUP_ID = 0
GROUP_START = {}    #每个group比赛是否开始
GROUP_CONNECT = {}  #每个group的所有conn
CONNECT_GROUP = {}  #conn所在的group
CONNECT_ANSWER = {} #conn是否已经正确回答问题

CONNECT_USERNAME = {}   #conn的username
GROUP_ANSWER = {}       #gruop的answer queue

HOST = '127.0.0.1'
PORT = 65432


class ThreadPoolManger():

	def __init__(self, thread_num):
		self.work_queue = queue.Queue()
		self.thread_num = thread_num

		for _ in range(thread_num):
			thread = ThreadManage(self.work_queue)
			thread.start()

	def add_job(self, func, *args):
		self.work_queue.put((func, args))


class ThreadManage(threading.Thread):

	def __init__(self, work_queue):
		threading.Thread.__init__(self)
		self.work_queue = work_queue
		self.daemon = True

	def run(self):
		while True:
			target, args = self.work_queue.get()
			target(*args)
			self.work_queue.task_done()


def handel_contest(group_id, contest_times):
	time.sleep(3)
	GROUP_ANSWER[group_id] = queue.Queue()
	member_num = (GROUP_CONNECT[group_id]).__len__()

	for i in range(int(contest_times)):
		num1 = random.randint(1, 100)
		num2 = random.randint(1, 100)
		question = str(num1) + "+" + str(num2) + "=?"
		standard_answer = num1 + num2
		for conn in GROUP_CONNECT[group_id]:
			CONNECT_ANSWER[conn] = False
			conn.sendall((wltp.response(response_type="message",
										json_data={"result": "success", "message": question}).getall()).encode())


		flag = 0
		start_time = time.time()
		while True:
			if time.time() - start_time > 1000000:
				for conn in GROUP_CONNECT[group_id]:
					conn.sendall((wltp.response(response_type="message",
												json_data={"result": "success",
														   "message": "time up!"}).getall()).encode())
				break
			if flag == member_num:
				break
			elif GROUP_ANSWER[group_id].empty():
				continue
			else:
				conn,answer =  GROUP_ANSWER[group_id].get()
				if answer == str(standard_answer):
					CONNECT_ANSWER[conn] = True
					score = (member_num - flag)
					send_msg = CONNECT_USERNAME[conn] + " has gained " + str(score) + " points!"

					for conn in GROUP_CONNECT[group_id]:
						conn.sendall((wltp.response(response_type="message",
													json_data={"result": "success",
															   "message": send_msg}).getall()).encode())
					flag += 1
				else:
					send_msg = CONNECT_USERNAME[conn] + "wrong! "
					for conn in GROUP_CONNECT[group_id]:
						conn.sendall((wltp.response(response_type="message",
													json_data={"result": "success",
															   "message": send_msg}).getall()).encode())

	for conn in GROUP_CONNECT[group_id]:
		conn.sendall((wltp.response(response_type="end",
										json_data={"result": "success"}).getall()).encode())



def handel_request(conn):
	global GROUP_ID

	while True:
		try:
			recv_data = conn.recv(1024).decode()
			print("thread {} is running".format(threading.current_thread().name))
			print(recv_data)
			recv_data = wltp.request(data=recv_data)
			if recv_data.error:
				conn.sendall((wltp.response(status="400 Bad Request").getall()).encode())
			else:
				if recv_data.request_type == "register":
					if recv_data.json_data["username"] in CONNECT_USERNAME.values():
						conn.sendall(
							(wltp.response(response_type="register",
										   json_data={"result": "username already exist"}).getall()).encode()
						)
					else:
						CONNECT_USERNAME[conn] = recv_data.json_data["username"]

				elif recv_data.request_type == "create":
					# 判断是否已注册
					if CONNECT_USERNAME[conn] == None:
						conn.sendall(
							(wltp.response(response_type="create",
										   json_data={"result": "please register first"}).getall()).encode())
					# 判断是否已经创建
					elif CONNECT_GROUP[conn] != None:
						conn.sendall((wltp.response(response_type="create",
													json_data={
														"result": "you have alerady created a group"}).getall()).encode())
					# 创建新的group
					else:
						while GROUP_ID in GROUP_CONNECT.keys():
							GROUP_ID += 1
							GROUP_ID %= 65535
						GROUP_CONNECT[GROUP_ID] = [conn]
						CONNECT_GROUP[conn] = GROUP_ID
						GROUP_START[GROUP_ID] = False
						conn.sendall((wltp.response(response_type="create",
													json_data={"result": "success",
															   "groupid": GROUP_ID}).getall()).encode())

				elif recv_data.request_type == "delete":  ####需要完善(creater的删除)
					# 判断是否已注册
					if CONNECT_USERNAME[conn] == None:
						conn.sendall(
							(wltp.response(response_type="delete",
										   json_data={"result": "please register first"}).getall()).encode())
					else:
						Group_id = CONNECT_GROUP[conn]
						# 判断是否拥有Group_id
						if Group_id == None:
							conn.sendall((
											 wltp.response(response_type="delete", json_data={
												 "result": "you are not the creater"}).getall()).encode())
							break
						else:
							# 判断是否为creater
							creater_conn = GROUP_CONNECT[Group_id][0]
							if conn != creater_conn:
								conn.sendall((wltp.response(response_type="delete",
															json_data={
																"result": "you are not the creater"}).getall()).encode())
							else:
								for connect in GROUP_CONNECT[Group_id]:
									connect.sendall(
										(wltp.response(response_type="delete",
													   json_data={"result": "success"}).getall()).encode())
								# 初始化成员的groupid,并删除该group
								for connect in GROUP_CONNECT[Group_id]:
									CONNECT_GROUP[connect] = None
								GROUP_CONNECT.pop(Group_id)

				elif recv_data.request_type == "join":
					# 判断是否已注册
					if CONNECT_USERNAME[conn] == None:
						conn.sendall(
							(wltp.response(response_type="join",
										   json_data={"result": "please register first"}).getall()).encode())
					# 判断是否已经加入了group
					elif CONNECT_GROUP[conn] != None:
						conn.sendall((wltp.response(response_type="join",
													json_data={
														"result": "you have already joined a group"}).getall()).encode())
					else:
						if int(recv_data.json_data["groupid"]) < 0:
							Group_id = random.choice(list(GROUP_CONNECT.keys()))
						else:
							Group_id = int(recv_data.json_data["groupid"])
						if Group_id == None:
							conn.sendall((wltp.response(response_type="join",
														json_data={
															"result": "there is no group available"}).getall()).encode())
						else:
							# 设置groupid并将conn加入到group中
							CONNECT_GROUP[conn] = Group_id
							GROUP_CONNECT[Group_id].append(conn)
							for connect in GROUP_CONNECT[Group_id]:
								connect.sendall((wltp.response(response_type="join",
															   json_data={"result": "success", "groupid": Group_id,
																		  "username": CONNECT_USERNAME[
																			  conn]}).getall()).encode())

				elif recv_data.request_type == "leave":
					# 判断是否已注册
					if CONNECT_USERNAME[conn] == None:
						conn.sendall(
							(wltp.response(response_type="leave",
										   json_data={"result": "please register first"}).getall()).encode())
					# 判断是否已经加入了group
					elif CONNECT_GROUP[conn] == None:
						conn.sendall(
							(wltp.response(response_type="leave",
										   json_data={"result": "you are not in any group"}).getall()).encode())
					else:
						# 初始化groupid并将该conn从当前group删除
						Group_id = CONNECT_GROUP[conn]
						CONNECT_GROUP[conn] = None
						GROUP_CONNECT[Group_id].remove(conn)
						for connect in GROUP_CONNECT[Group_id]:
							connect.sendall((wltp.response(response_type="leave",
														   json_data={"result": "success", "groupid": Group_id,
																	  "username": CONNECT_USERNAME[
																		  conn]}).getall()).encode())

				elif recv_data.request_type == "start":
					# 判断是否已注册
					if CONNECT_USERNAME[conn] == None:
						conn.sendall(
							(wltp.response(response_type="delete",
										   json_data={"result": "please register first"}).getall()).encode())
					# 判断是否为creater
					else:
						Group_id = CONNECT_GROUP[conn]
						# 判断是否拥有Group_id
						if Group_id == None:
							conn.sendall(
								(wltp.response(response_type="delete",
											   json_data={"result": "you are not the creater"}).getall()).encode())
							break
						else:
							creater_conn = GROUP_CONNECT[Group_id][0]
							if conn != creater_conn:
								conn.sendall((wltp.response(response_type="start", json_data={
									"result": "you are not the creater"})).getall().encode())
							else:
								for connect in GROUP_CONNECT[Group_id]:
									connect.sendall((wltp.response(response_type="start", json_data={"result": "success",
																							  "contest_times":
																								  recv_data.json_data[
																									  "contest_times"]})).getall().encode())
								thread_pool.add_job(handel_contest, *(Group_id, recv_data.json_data["contest_times"]))

				elif recv_data.request_type == "submit":
					# 判断是否已注册
					if CONNECT_USERNAME[conn] == None:
						conn.sendall(
							(wltp.response(response_type="submit",
										   json_data={"result": "please register first"}).getall()).encode())
					# 判断是否已经加入了group
					elif CONNECT_GROUP[conn] == None:
						conn.sendall(
							(wltp.response(response_type="submit",
										   json_data={"result": "you are not in any group"}).getall()).encode())
					else:
						Group_id = CONNECT_GROUP[conn]
						# 判断比赛是否开始
						if GROUP_START[Group_id] == False:
							conn.sendall(
								(wltp.response(response_type="submit",
											   json_data={"result": "the contest hasn’t start"}).getall()).encode())
						else:
							GROUP_ANSWER[Group_id].put([conn,recv_data.json_data["answer"]])


		except ConnectionResetError:
			print(repr(conn) + "已强制断开连接")
			Group_id = CONNECT_GROUP[conn]
			# 判断断连者是否为creater
			if GROUP_CONNECT[Group_id][0] == conn:
				for connect in GROUP_CONNECT[Group_id]:
					CONNECT_GROUP[connect] = None
				GROUP_CONNECT.pop(Group_id)

			else:
				GROUP_CONNECT[Group_id].remove(conn)
			CONNECT_GROUP.pop(conn)
			CONNECT_USERNAME.pop(conn)
			break

	conn.close()


if __name__ == "__main__":

	print("Server is starting")

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.bind((HOST, PORT))

	sock.listen(65535)

	print("Server is listening port {},with max connection 4".format(PORT))

	thread_pool = ThreadPoolManger(4)

	try:
		while True:
			conn, addr = sock.accept()
			CONNECT_GROUP[conn] = None
			CONNECT_USERNAME[conn] = None
			thread_pool.add_job(handel_request, *(conn,))
	except:
		sock.close()
