angular
	.module("macmonApp")
	.controller("Macs.IndexController", Controller);

 function Controller($http, $log) {

 	var vm = this;
 	vm.confirmUpdate = confirmUpdate;
 	vm.loading = [];

 	initController();

 	function initController() {

		// console.log("MacListCtrl");

		$http.get("/macs?order=status").then(
			function(res) {
				// console.log(res);
				vm.macsCollection = res.data;
			},
			function(err) {
				console.log(err);
			}
		)

	}

	function confirmUpdate(mac_id, status, $index) {
 		vm.loading[$index] = true;

 		var data = {
 			status: status,
 		};

 		$http.patch(`/macs?id=eq.${mac_id}`, data).then(
 			function(res) {
 				// console.log(res);
 				vm.loading[$index] = false;
 				vm.macsCollection[$index].status = status;
 			},
 			function(err) {
 				console.log(err);
 			}
 		)

 	}

};
