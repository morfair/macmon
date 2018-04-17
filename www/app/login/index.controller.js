angular
	.module("macmonApp")
	.controller("Login.IndexController", Controller);


 function Controller($location, AuthenticationService) {

 	var vm = this;

 	vm.login = login;

 	initController();



 	function initController() {

		console.log("LoginCtrl");

		// reset login status
		AuthenticationService.Logout();
	
	};



	function login() {

		vm.loading = true;
		AuthenticationService.Login(vm.username, vm.password, function(result) {

			if ( result == true ) {
				$location.path("/");

			} else {

				vm.error = "Username or password is incorrect";
				vmloading = false;
				
			}
		});

	};



};