
let cardContainers = [...document.querySelectorAll('.card-container')]
let first_buttons = [...document.querySelectorAll('.pre')]
let next_buttons = [...document.querySelectorAll('.nxt')]

cardContainers.forEach((item, i) => {
    let containerDim = item.getBoundingClientRect()
    let containerWid = containerDim.width

    next_buttons[i].addEventListener('click', () => {
        item.scrollLeft += containerWid - 100;
    })

    first_buttons[i].addEventListener('click', () => {
        item.scrollLeft -= containerWid + 100;
    })
})