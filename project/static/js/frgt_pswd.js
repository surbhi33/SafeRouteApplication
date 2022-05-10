var btn = document.getElementById("button")
var lab = document.getElementById("msg")
var typ = document.getElementById("email")
typ.setAttribute("type","email")
btn.addEventListener("click",() =>{

    if (lab.innerText == 'Enter your registered email address to receive a six digit code') {
        typ.value = ''
        lab.innerText = 'Enter the six digit code'
        typ.setAttribute("type","text")
    }

    else if (lab.innerText == 'Enter the six digit code'){
        typ.value = ''
        lab.innerText = 'Enter new password'
        typ.setAttribute("type","password")
    }

    else if (lab.innerText == 'Enter new password'){
        alert('password reset successful')
        window.location.href = "/"
    }
    
});