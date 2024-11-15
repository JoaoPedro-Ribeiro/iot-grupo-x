const ipRasp = '192.168.0.243'
const client = mqtt.connect(`ws://${ipRasp}:9001`);

client.on('connect', function () {
    console.log('Conectado ao broker MQTT!');
    client.subscribe('esteira/status', function (err) {
        if (!err) {
            console.log('Inscrito no tópico "esteira/status"');
        }
    });
});

client.on('message', function (topic, message) {
    console.log('Mensagem recebida: ' + message.toString());
    
    const status = message.toString();

    if (status === 'parada') {
        document.getElementById("ledStatus").textContent = "Esteira Parada!";
        document.getElementById("ledStatus").style.color = "red";
        document.getElementById("reiniciarBtn").disabled = false;
    } else if (status === 'funcionando') {
        document.getElementById("ledStatus").textContent = "Esteira Funcionando!";
        document.getElementById("ledStatus").style.color = "green";
        document.getElementById("reiniciarBtn").disabled = false;
    } else if (status === 'aguardando') {
        document.getElementById("ledStatus").textContent = "Aguardando...";
        document.getElementById("ledStatus").style.color = "#555";
        document.getElementById("reiniciarBtn").disabled = true;
    }
    else if (status === 'reiniciando') {
        document.getElementById("ledStatus").textContent = "Reiniciando...";
        document.getElementById("ledStatus").style.color = "yellow";
        document.getElementById("reiniciarBtn").disabled = true;
    }
});

document.getElementById("reiniciarBtn").addEventListener("click", function() {
    console.log("Reiniciando a esteira...");
    client.publish('esteira/reiniciar', 'reiniciar', { qos: 1 });
    
    this.disabled = true;
    document.getElementById("ledStatus").textContent = "Aguardando...";
    document.getElementById("ledStatus").style.color = "#555";
});
