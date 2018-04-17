angular
	.module("macmonApp")
	.factory('AuthenticationService', Service);


function Service($http, $localStorage) {
	
	var service = {};

	service.Login = Login;
	service.Logout = Logout;

	return service;


	function Login(email, password, callback) {

        var data = { "email": email, "pass": password };
        console.log(data);

		$http.post("/rpc/login", data).then(
			function (res) {

                console.log(res);

				// login successful if there's a token in the response
				if (res.status == 200) {

                    var token = res.data[0].token;
				
					// store username and token in local storage to keep user logged in between page refreshes
					$localStorage.currentUser = { email: email, token: token };

					// add jwt token to auth header for all requests made by the $http service
					$http.defaults.headers.common.Authorization = 'Bearer ' + token;

					// execute callback with true to indicate successful login
					callback(true);
				
				} else {

					// execute callback with false to indicate failed login
					callback(false);
				}
			},
			function(err) {
				console.log(err);
			});
	};


	function Logout() {

		// remove user from local storage and clear http auth header
		delete $localStorage.currentUser;
		$http.defaults.headers.common.Authorization = '';
    };


};
