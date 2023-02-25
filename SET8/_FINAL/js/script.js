$(document).ready(function () {
    // Activate Carousel with a specified interval
    $("#mainSlider").carousel({ interval: 1000 });

    for (let i = 0; i < 4; i++) {
        $("#ind_" + i.toString()).click(function () {
            $("#mainSlider").carousel(i);
        });
    }

    // Enable Carousel Controls
    $(".carousel-control-prev").click(function () {
        $("#mainSlider").carousel("prev");
    });
    $(".carousel-control-next").click(function () {
        $("#mainSlider").carousel("next");
    });

});


let btns = document.getElementsByClassName("main-btn");

for (let i = 0; i < 4; i++) {
    let color;
    switch (i) {
        case 0:
            color = "#636BAE";
            break
        case 1:
            color = "#BB8ABA";
            break
        case 2:
            color = "#E6E177";
            break
        case 3:
            color = "#E98F89";
    }

    btns[i].onmouseover = function () {
        btns[i].style.cssText += 'color: #FFF;text-decoration: none; border-color:' + color + '; background-color:transparent';
    };

    btns[i].onmouseout = function () {
        btns[i].style.cssText += 'border-color:transparent; background-color:#3f3b3b';
    };
}