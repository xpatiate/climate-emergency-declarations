'use strict';

var showing = {};
$(document).ready(() => {
    $('button.view-structure').click(toggleEditOptions);
    $('button.view-area').click(toggleEditOptions);

    $('div.delete-link').click(deleteThis);
    $('div.bulk-edit').click(enableBulkEdit);
    $('.bulk-edit-item').hover(highlightRow);
    $('.bulk-edit-item').click(selectRow);
    $('#bulk-edit-select').click(selectAll);

    let toggleInboxEl = $('.toggle-inbox');
    
    if (toggleInboxEl.length > 0) {
        if (localStorage.getItem('inbox') == 'hidden') {
            toggleInbox();
        }
        
        toggleInboxEl.click(toggleInbox);
    }
    
    $('.inbox-paste textarea').bind('paste', pasteInbox);
});

function selectAll(ev) {
    $('.bulk-edit-item').prop('checked', true)
    $('.bulk-edit-go').css('visibility','visible')
    return false;
}

function highlightRow(ev) {
    var el = ev.target;
    var tableRow = $(el.parentElement.parentElement);
    tableRow.toggleClass('hover-highlight')
}
function selectRow(ev) {
    var el = ev.target;
    var tableRow = $(el.parentElement.parentElement);
    tableRow.toggleClass('select-highlight')
    $('.bulk-edit-go').css('visibility','visible')
}

function enableBulkEdit(ev) {
    var el = ev.target;
    $('.bulk-edit-item').css('visibility','visible')
    $('.bulk-edit-extra').css('visibility','visible')
/*
   var editBoxes = $('.bulk-edit-item')
    editBoxes.each(function(i, box) {
	console.log(box)
	box.css('visibility','visible')
    });
    */
    return false;
}

function toggleEditOptions(ev) {
    var el = ev.target;
    var editdivid = el.id.replace('view','edit');
    var editdiv = $( '#' + editdivid );
    if (showing[el.id] == 1) {
        editdiv.css('display','none');
        showing[el.id] = 0;
        el.innerHTML = '*';
    } else {
        editdiv.css('display','block');
        showing[el.id] = 1;
        el.innerHTML = '-';
    }
	return false;
}

function deleteThis(ev) {
    ev.preventDefault()
    var el = ev.target;
    var parentDiv = el.parentElement;
    var apiUrl = parentDiv.dataset.url;
    var objType = parentDiv.dataset.type;
    const response = confirm('Are you sure you want to delete this ' + objType + '?');
    if (response) {
        console.log('making API call to ' + apiUrl);
        //TODO make this a POST with CSRF
        var oReq = new XMLHttpRequest();
        oReq.onreadystatechange = () => {
            if (oReq.readyState === 4) {
                console.log(oReq);
                if (oReq.status == '200') {
                    window.location.reload();
                } else {
                    alert("operation failed");
                }
            }
        }
        oReq.open("GET", apiUrl);
        oReq.send();
    }
};

function toggleInbox() {
    let inbox = $('.inbox-heading, .inbox-list');
    if (inbox.css('display') == 'none') {
        inbox.css('display', 'block');
        $('.toggle-inbox').html('hide inbox');
        localStorage.setItem('inbox', 'shown');
    } else {
        inbox.css('display', 'none');
        $('.toggle-inbox').html('show inbox');
        localStorage.setItem('inbox', 'hidden');
    }
}

function selectInboxItem(ev) {
    let deselect = false;
    for (let row = 0; row < ev.target.parentElement.parentElement.children.length; row++) {
        if (ev.target.parentElement.parentElement.children[row].getAttribute('id') == ev.target.parentElement.getAttribute('id') && ev.target.parentElement.getAttribute('id')) {
            deselect = true;
        }
        
        ev.target.parentElement.parentElement.children[row].removeAttribute('id');
    }

    if (deselect) {
        document.querySelectorAll('.add-from-inbox, .dec-from-inbox').forEach((el) => {
            el.removeAttribute('href');
        });
    } else {
        ev.target.parentElement.setAttribute('id', 'selected-inbox-item');
    
        document.querySelectorAll('.add-from-inbox, .dec-from-inbox').forEach((el) => {
            let url = el.getAttribute('data-url')
            el.setAttribute('href', url.substring(0, url.length - 1) + ev.target.parentElement.getAttribute('data-id'));
        });
    }
}

function pasteInbox(ev) {
    let html = ev.originalEvent.clipboardData.getData('text/html');
    
    let data = tableToCSV(html, '|');
    
    if (data) {
        ev.preventDefault();
        ev.target.value = data;
        ev.target.style.height = '1px';
        ev.target.style.height = (2 + ev.target.scrollHeight) + 'px';
    }
}

function tableToCSV(input, separator, split_links=false) {
    let pastedElement = document.createElement('html');
    pastedElement.innerHTML = input;

    let table = pastedElement.querySelector('tbody');
    
    if (!table) {
        table = pastedElement.querySelector('table');
    }
    
    let values = [];
    
    if (table != null) {
        for (let row = 0; row < table.children.length; row++) {
            values[row] = [];
            for (let cell = 0; cell < table.children[row].children.length; cell++) {
                if (split_links) {
                    let link = table.children[row].children[cell].querySelector('a');
                    
                    if (link) {
                        values[row].push(link.textContent);
                        values[row].push(link.getAttribute('href'));
                    } else {
                        values[row].push(table.children[row].children[cell].textContent);
                    }
                } else {
                    values[row].push(table.children[row].children[cell].textContent);
                }
            }
        }
        return values.map((row) => row.join(separator)).join('\n');
    } else {
        return false;
    }
}

/* 
Process for multiple area creation:

User clicks "quick add multiple" link, which fires showMultiAddForm()
  -> Display form containing textarea with action specifying IDs
  -> Attach paste event listener to textarea
User pastes HTML into textarea, which fires getPastedHTML()
  -> Extract HTML from clipboard data, or plain text if there is no HTML
  -> If HTML contains a table
    -> Send HTML to API to extract areas
    -> If API returns a good response, replace textarea contents with API response
User clicks 'create' button, form submits - no JS nivolved
  -> Submit form to API which parses textarea data and creates areas
*/
    
function getPastedHTML(ev) {
    let html = ev.originalEvent.clipboardData.getData('text/html');
    
    let data = tableToCSV(html, '|', true);
    
    if (data) {
        ev.preventDefault();
        ev.target.value = data;
    }
}

// Simple function to display the textarea when link is clicked,
// and attach a paste event listener
function showMultiAddForm(target_id) {
    var target = $( '#' + target_id);
    if (target.css('display') != 'inline') {
        target.css('display', 'inline');
        target.on('paste', getPastedHTML);
    } else {
        target.css('display', 'none');
        target.off('paste', getPastedHTML);
    }
    return false;
}
