import requests
import json
from typing import Union,Literal,Any

class MoodleError(Exception):
    def __init__(self, error, errorcode=None, stacktrace=None, debuginfo=None, reproductionlink=None):
        self.error = error
        self.errorcode = errorcode
        self.debuginfo = debuginfo
        self.stacktrace = stacktrace
        self.reproductionlink = reproductionlink
        super().__init__(f"Moodle Error: {self.errorcode} {self.error}")

class MoodleException(Exception):
    def __init__(self, exception, errorcode=None, message=None, debuginfo=None):
        self.exception = exception
        self.errorcode = errorcode
        self.message = message
        self.debuginfo = debuginfo
        if self.message and self.debuginfo:
            super().__init__(f"Message: {self.message} DebugInfo:{self.debuginfo}")
        elif self.message:
            super().__init__(f"Message: {self.message}")
        elif self.debuginfo:
            super().__init__(f"DebugInfo: {self.debuginfo}")
        else:
            super().__init__(f"Generic MoodleException")

class MoodleWebServiceAPIClient():
    _HEADERS = {
        'accept': 'application/json',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'CSE Dept Attendance App',
    }

    def __init__(self,token=None,username=None,password=None,api_base = None) -> None:
        if not (token or (username and password)):
            raise ValueError("Either token or both username and password must be provided.")
        if not api_base:
            raise ValueError("API Endpoint must be provided.")

        self.API_BASE = api_base
        self.TOKEN = token
        self.CLIENT_USER_DATA = None

        if not self.TOKEN:
            self.TOKEN = self._authenticate(username,password)

        self._set_client_user_data(force=True)

    def _authenticate(self, username:str, password:str) -> str:
        data = {
            'moodlewsrestformat': 'json',
            'username': username,
            'password': password,
            "service": "moodle_mobile_app"
        }
        response = requests.post(f'{self.API_BASE}/login/token.php', data=data, headers=self._HEADERS)
        response.raise_for_status()  # Handle potential HTTP errors
        response_json = response.json()
        if "error" in response_json:
            raise MoodleError(**response_json)
        elif "exception" in response_json:
            raise MoodleException(**response_json)

        return response_json["token"]

    def _api_call(self, wsfunction:str, data:dict) -> dict:
        data['wstoken'] = self.TOKEN
        data['wsfunction'] = wsfunction
        data['moodlewsrestformat']="json"
        response = requests.post(f'{self.API_BASE}/webservice/rest/server.php', data=data,headers=self._HEADERS)
        response.raise_for_status()  # Handle potential HTTP errors
        response_json = response.json()
        if "error" in response_json:
            raise MoodleError(**response_json)
        elif "exception" in response_json:
            raise MoodleException(**response_json)
        return response_json

    def _set_client_user_data(self,force:bool=False) -> None:
        if force==True or self.CLIENT_USER_DATA is None:
            self.CLIENT_USER_DATA = self._api_call("core_webservice_get_site_info",{})

    @classmethod
    def _flatten_rest_api_arguments(cls,arguments:Any,flattened_dict:dict={},parent_obj_prefix:str="") -> dict:

        if not isinstance(arguments,(list,dict)):
            flattened_dict[parent_obj_prefix] = arguments
            return flattened_dict

        if isinstance(arguments,list):
            for idx,item in enumerate(arguments):
                new_parent_obj_prefix = f"{parent_obj_prefix}[{idx}]" if parent_obj_prefix else f"{idx}"
                cls._flatten_rest_api_arguments(item,flattened_dict,new_parent_obj_prefix)
        if isinstance(arguments,dict):
            for key,value in arguments.items():
                new_parent_obj_prefix = f"{parent_obj_prefix}[{key}]" if parent_obj_prefix else f"{key}"
                cls._flatten_rest_api_arguments(value,flattened_dict,new_parent_obj_prefix)

        return flattened_dict


    def get_user_courses(self,userid:Union[str,int],returnusercount:Literal[0,1]=0) -> list:
        data = {
            'userid': userid,
            'returnusercount':returnusercount
        }
        return self._api_call("core_enrol_get_users_courses",data)

    def get_course_enrolled_users(self,courseid:Union[str,int],options:list[dict[Literal["name","value"],str]]=[{"name":"userfields","value":"(idnumber,roles,email,username)"}]) -> list:
        data = {'courseid': courseid}
        data = self._flatten_rest_api_arguments({"options":options},flattened_dict=data)
        return self._api_call("core_enrol_get_enrolled_users",data)

if __name__=="__main__":
    client = MoodleWebServiceAPIClient(
        # username="student1",
        username="teacher@teacher.com",
        password="aA1!22334455",
        api_base="http://localhost:8080")
    client_courses = client.get_user_courses(client.CLIENT_USER_DATA["userid"])
    client_courses.sort(key = lambda course:course["startdate"],reverse=True)
    course = client_courses[0]
    enrolled_users = client.get_course_enrolled_users(course["id"])

    faculty = [user for user in enrolled_users if any(role["roleid"] < 5 for role in user["roles"])]
    students = sorted([user for user in enrolled_users if user not in faculty],key=lambda user:user["fullname"].upper()) # ideally should use user["idnumber"] to sort.

    print(json.dumps(students,indent=4))
