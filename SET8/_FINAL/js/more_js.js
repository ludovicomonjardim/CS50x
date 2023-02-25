$( document ).ready(function() {

    // Progress bar

    let vcontainers = [["circleA", 25], ["circleB", 50], ["circleC", 75], ["circleD", 100]]
    for (let i = 0; i < 4; i++) {
        vcontainers[i].push(document.getElementById(vcontainers[i][0]));
        vcontainers[i].push(new ProgressBar.Circle(vcontainers[i][2], {
            color: '#65DAF9',
            strokeWidth: 8,
            duration: 50 * vcontainers[i][1],
            from: { color: '#aaa' },
            to: { color: '#65DAF9' },
            step: function (state, circle) {
                circle.path.setAttribute('stroke', state.color);
                var value = Math.round(circle.value() * vcontainers[i][1]);
                circle.setText(value);
            }
        }));
    }

    let dataAreaOffset = $('#progressbar').offset();

    // stop so animation runs only once
    let stop = 0;
    $(document).ready(function () {
        let scroll = $(window).scrollTop();
        if (scroll > (dataAreaOffset.top - 500) && stop == 0) {
            for (let i = 0; i < 4; i++) {
                vcontainers[i][3].animate(1.0);
            }
            stop = 1;
        }
    });
});