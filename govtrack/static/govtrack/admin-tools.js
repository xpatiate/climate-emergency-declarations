'use strict';

var showing = {};
$(document).ready(() => {
    $('button.view-structure').click(toggleEditOptions);
    $('button.view-area').click(toggleEditOptions);

    $('div.delete-link').click(deleteThis);

    $('.toggle-bin').click(toggleBin);
    $('.bin textarea').bind('paste', pasteBin);

    if (localStorage.getItem('bin') == 'shown') {
        toggleBin();
    }
});

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

function toggleBin() {
    let bin = $('.bin');
    if (bin.css('display') == 'none') {
        bin.css('display', 'block');
        $('.toggle-bin').html('hide bin');
        localStorage.setItem('bin', 'shown');
    } else {
        bin.css('display', 'none');
        $('.toggle-bin').html('show bin');
        localStorage.setItem('bin', 'hidden');
    }
}

function selectBinItem(ev) {
    for (let row = 0; row < ev.target.parentElement.parentElement.children.length; row++) {
        ev.target.parentElement.parentElement.children[row].removeAttribute('id');
    }
    
    ev.target.parentElement.id = 'selected-bin-item';

    document.querySelectorAll('.add-from-bin, .dec-from-bin').forEach((el) => {
        let url = el.getAttribute('data-url')
        el.setAttribute('href', url.substring(0, url.length - 1) + ev.target.parentElement.getAttribute('data-id'));
    });
}

function pasteBin(ev) {
    let html = ev.originalEvent.clipboardData.getData('text/html');
    
    let data = tableToCSV(html);
    
    if (data) {
        ev.preventDefault();
        ev.target.value = data;
        ev.target.style.height = '1px';
        ev.target.style.height = (2 + ev.target.scrollHeight) + 'px';
    }
}

function tableToCSV(input) {
    let pastedElement = document.createElement('html');
    pastedElement.innerHTML = input;

    let table = pastedElement.querySelector('tbody');
    
    if (!table) {
        table = pastedElement.querySelector('table');
    }
    
    let values = [];
    
    if (table != null) {
        for (let row = 0; row < table.children.length; row++) {
            values[row] = []
            for (let cell = 0; cell < table.children[row].children.length; cell++) {
                values[row][cell] = table.children[row].children[cell].textContent
            }
        }
        return values.map((row) => row.join('|')).join('\n');
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
    
function getPastedHTML(e) {
    e.preventDefault();
    var target = $(e.target)
    var pastedText = ''
    // try to get HTML-formatted text from clipboard event
    if (e.originalEvent.clipboardData && e.originalEvent.clipboardData.getData) {
        pastedText = e.originalEvent.clipboardData.getData('text/html');
    }
    // If none, try to get plain text
    if (pastedText == '') {
        pastedText = e.originalEvent.clipboardData.getData('text/plain');
    }
    target.html(pastedText)
    // If pastedText looks like HTML and contains a <table>,
    // call extractPastedData
    var dom_areas = $($.parseHTML(pastedText))
    var table_area = dom_areas.closest('table');
    if (table_area.length) {
        extractPastedData(target)
    }
    // otherwise we just leave the pasted text in the textarea
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
    }
    return false;
}

// After HTML text is pasted, send it to the API to extract the areas and URLs
// Replace the textarea contents with the API response
function extractPastedData(target) {
    var pastedText = target.html()
    jQuery.ajax('/api/extract_areas', {
        'method': 'POST',
        'data': {
            'area_table': pastedText,
        },
        'success': function(response) {
            target.html(response['areas'])
        }
    });
}
