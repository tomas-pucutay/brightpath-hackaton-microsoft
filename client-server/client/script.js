const readButton = document.getElementById('readButton');
const socket = io.connect('http://localhost:5000');

readButton.addEventListener('click', function(event) {
    event.preventDefault();

    const lang = "{'es-ES':'es'}"
    const text = document.getElementById('text').innerText;
    socket.emit('create_audio', { text: text, lang: lang });

    socket.on('audio_created', function(data) {
        console.log(data.message);
    });

    socket.emit('start_audio', { isPlaying: true, enableSpace:true, enableControl: false });

    socket.on('audio_started', function(data) {
        console.log(data.message);
    });

});

document.addEventListener('keydown', function(event) {
    if (event.code === 'Space') {
        socket.emit('space_pressed');
    } else if (event.code === 'ControlLeft' || event.code === 'ControlRight') {
        socket.emit('control_pressed');
    } else if (event.code === 'Enter') {
        socket.emit('enter_pressed');
    }
});