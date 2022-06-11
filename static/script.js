/* ====== View Attachment Btn toggle ======*/
function toggleText(e){
  (e.textContent == 'View Attachments')? e.textContent = 'Hide Attachments': e.textContent = 'View Attachments';
}
/* ====== View Attachment Btn toggle ======*/

/* ====== parse mailbox name ======*/
function parseMailbox(mailbox){
    mailbox = mailbox.trim()
    if(mailbox[0] == '&')
      mailbox = mailbox.slice(5, -5)
    mailbox = mailbox.split('$').pop()
    return mailbox
}
/* ====== parse mailbox name ======*/

/* ====== Loader ======*/
function loading() {
    document.getElementById('body').style.pointerEvents = "none";
    document.getElementById('loading').style.display = "block";
}
/* ====== Loader ======*/

/* ====== Reset form on back arrow ======*/
window.addEventListener("pageshow", function(event){
    document.getElementById('body').style.pointerEvents = "auto";
    document.getElementById('loading').style.display = "none";
    var forms = document.getElementsByTagName("form");
    for(let i = 0; i < forms.length; i++){
      forms[i].reset();
    }
});
/* ====== Reset form on back arrow ======*/