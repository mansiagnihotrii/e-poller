
var i = 3; 
function increment(){
i += 1; 
}

function createEl() {

var div = document.createElement('div');
var input = document.createElement("INPUT");
var label = document.createElement("Label");

//Label
label.setAttribute("for","option"+i);
label.setAttribute("class","sr-only");
label.innerHTML = "Option "+i+" ";

//input
input.setAttribute("type", "text");
input.setAttribute("id","option"+i);
input.setAttribute("Name", "option");
input.setAttribute("class","form-control");
input.setAttribute("placeholder", "Option "+i);

increment();

//div
div.setAttribute("class","form-group has-success");
div.appendChild(label);
div.appendChild(input);


document.getElementById("new").appendChild(div);
}
