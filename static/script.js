document.getElementById("verificar-form").addEventListener("submit", function(event) {
    event.preventDefault();
    
    var cnpj = document.getElementById("cnpj").value;
    
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/verificar");
    xhr.setRequestHeader("Content-Type", "application/json");
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                showResult(response);
            } else {
                console.error("Erro na requisição: " + xhr.status);
            }
        }
    };
    
    xhr.send(JSON.stringify({cnpj: cnpj}));
});

function showResult(response) {
    var resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "";
    
    if (response.error) {
        resultDiv.innerHTML = "<p class='error'>" + response.error + "</p>";
    } else {
        resultDiv.innerHTML = "<p class='success'>A empresa pode ser dispensada de licenciamento</p>";
        resultDiv.innerHTML += "<p>CNAEs Encontrados:</p>";
        
        var cnaes = response.cnaes;
        var cnaesList = document.createElement("ul");
        
        cnaes.forEach(function(cnae) {
            var cnaeItem = document.createElement("li");
            cnaeItem.textContent = cnae;
            cnaesList.appendChild(cnaeItem);
        });
        
        resultDiv.appendChild(cnaesList);
    }
}