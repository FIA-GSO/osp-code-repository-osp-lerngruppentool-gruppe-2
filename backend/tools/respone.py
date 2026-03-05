
from tools.logger import log


class Response:
	def __init__(self, status: str = "success", message: str = "", data=None):
		self.status = status
		self.message = message
		self.data = data

	def to_dict(self):
		resp = {
			"status": self.status,
			"message": self.message
		}
		if self.data is not None:
			resp["data"] = self.data
		return resp

	@staticmethod
	def ok(data=None, message=""):
		return Response("success", message, data).to_dict()

	@staticmethod
	def error(message, data=None):
		log(f"Response error: {message}", "error")
		return Response("error", message, data).to_dict()
