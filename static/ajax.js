function fetchHeaders(mailbox) {
  const loadMoreBtn = document.getElementById('loadMoreBtn')
  loadMoreBtn.classList.add('disabled')
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function () {
    let lastIdx = 2;
    if (this.readyState == 4 && this.status == 200) {
      const data = JSON.parse(this.responseText);
      // console.log(typeof(data))
      const headers = data.headers;
      for (let i = 0; i < headers.length; i++) {
        // console.log("inside for loop")
        let table = document.getElementById("headers");
        let row = document.createElement('tr');
        let col = document.createElement('td');
        let a = document.createElement('a');
        a.href = `/${mailbox}/${headers[i].index}`;
        a.onclick = () => loading();
        let card = document.createElement('div');
        card.classList.add('card');
        let cardBody = document.createElement('div');
        cardBody.classList.add('card-body');
        
        let cardTitle = document.createElement('div');
        cardTitle.classList.add('card-title', 'd-flex', 'justify-content-between');
        let div1 = document.createElement('div');
        div1.innerHTML = `<b>From:</b> ${headers[i].From}`;
        let div2 = document.createElement('div');
        div2.innerHTML = `<b>${headers[i].index}</b>`
        cardTitle.appendChild(div1)
        cardTitle.appendChild(div2)

        let cardTitle2 = document.createElement('div');
        cardTitle2.classList.add('d-flex', 'justify-content-between', 'align-items-center');
        let div3 = document.createElement('div');
        div3.innerHTML = `<b>Subject:</b> ${headers[i].Subject}`;
        let div4 = document.createElement('div');
        div4.classList.add('text-muted');
        div4.innerHTML = `<b>Date:</b> ${headers[i].Date}`;
        cardTitle2.appendChild(div3);
        cardTitle2.appendChild(div4);


        cardBody.appendChild(cardTitle)
        cardBody.appendChild(cardTitle2)

        card.appendChild(cardBody);
        a.appendChild(card)

        col.appendChild(a);
        row.appendChild(col);
        table.appendChild(row);

        lastIdx = `${headers[i].index}` 
      }
      loadMoreBtn.classList.remove('disabled')
      if(lastIdx <= 1){
        const loadMore = document.getElementById('loadMore');
        loadMore.style.display = "none";
      }
    }
  };
  
  xhttp.open("POST", `/open_mailbox/${mailbox}`, true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send();
}

