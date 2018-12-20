import json

class request:
	def __init__(self,url=None,protocol_version="WLTP/1.1",request_type="",json_data=None,data=None):
		self.error = False
		if data!=None:
			self.data = data
			data = data.split("\r\n")
			try:

				self.url,self.protocol_version = data[0].split(" ")
				self.request_type = data[1].split(":")[1]
				if self.request_type not in ["register","create","delete" ,"start","end","join","leave","submit"]:
					print("11111")
					self.error = True
				else:

					print(data)

					if len(data)==3 and data[2]!="":
						self.json_data = json.loads(data[2])
					if data[1].split(":")[0]!="Request-Type":
						print("22222222")
						self.error = True
					elif len(data)>3:
						print("333333333")
						self.error = True



			except Exception as e:
				print(e)
				self.error = True
			print(self.error)
		else:
			self.url = url
			self.protocol_version = protocol_version
			self.request_type = request_type
			if json_data!=None:
				self.json_data = json_data

				self.data = self.url + " " + self.protocol_version + "\r\n" + "Request-Type:" + self.request_type + "\r\n" + json.dumps(self.json_data)
			else:

				self.data = self.url + " " + self.protocol_version + "\r\n" + "Request-Type:" + self.request_type + "\r\n"

	def getall(self):
		return self.data

class response:
	def __init__(self,protocol_version="WLTP/1.1",status="200 OK",response_type="",json_data=None,data=None):
		print(data)
		if data!=None:
			self.data = data
			data = data.split("\r\n")
			tmp = data[0].split(" ")
			self.protocol_version = tmp[0]
			self.status = " ".join(tmp[1:])
			self.response_type = data[1].split(":")[1]
			if len(data)==3 and self.status=="200 OK":
				print(data[2])
				self.json_data = json.loads(data[2])

		else:
			self.status = status
			self.protocol_version = protocol_version
			self.response_type = response_type
			if json_data!=None:
				self.json_data = json_data
				self.data = self.protocol_version + " " + self.status + "\r\n" + "Response-Type:" + self.response_type + "\r\n" + json.dumps(self.json_data)
			else:
				self.data = self.protocol_version + " " + self.status + "\r\n" + "Response-Type:" + self.response_type + "\r\n"

	def getall(self):
		return self.data

# a = response(data="WLTP/1.1 200 OK\r\nMessage-Type:login\r\n"+json.dumps( {"username":"xl","password":"123"} ))
# print(a.json_data["username"])