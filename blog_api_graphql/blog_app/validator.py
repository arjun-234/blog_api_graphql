from django.contrib.auth.models import User
import re
from django.db.models import Q

class Validator:
	def validate_username(self,username,id=None):
		# same username checker
		if id:
			if User.objects.filter( ~Q(id=id) & Q(username=username)).exists():
				response = {'msg':'user with same username exists','is_valid':False}
				return response
		else:
			if User.objects.filter(username=username).exists():
				response = {'msg':'user with same username exists','is_valid':False}
				return response

        # username validator
		if not re.match(r'^(?![_.@+-])[a-zA-Z0-9_.@+-]{5,20}$',username):
			msg = {'username':["1)Username must be 5-20 characters long",\
				"2) Username may only contain:","- Uppercase and lowercase letters","- Numbers from 0-9 and",\
				"- Special characters _.+-@","3) Username may not:Begin or finish with _.+-@ "]}

			response = {'msg':msg,'is_valid':False}
			return response

		response = {'msg':'valid username','is_valid':True}
		return response

    # first_name and last_name validator
	def validate_name(self,first_name,last_name):
		if len(first_name.strip()) == 0:
			response = {'msg':"first_name must not be blank", 'is_valid':False}
			return response

		if len(last_name.strip()) == 0:
			response = {'msg':"last_name must not be blank", 'is_valid':False}
			return response

		if first_name.strip() == last_name.strip():
			response = {'msg':"first_name and last_name must be diffrent", 'is_valid':False}
			return response
		response = {'msg':"valid name", 'is_valid':True}
		return response

    # email validator
	def validate_email(self,email):
		if not re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',email):
			response = {'msg':"invalid email", 'is_valid':False}
			return response
		response = {'msg':"valid email", 'is_valid':True}
		return response

	def validate_password(self,password):
		# password validator
		if not re.match(r"^(?=.*[\d])(?=.*[A-Z])(?=.*[a-z])(?=.*[@#$])[\w\d@#$]{6,12}$",password):
			msg = {'password':["at least one digit","at least one uppercase letter","at least one lowercase letter","at least one special character[$@#]"]}
			response = {'msg':msg,'is_valid':False}
			return response
		response = {'msg':'valid password','is_valid':True}
		return response