'use strict';

var showing = {};
$(document).ready(() => {
    $('button.view-structure').click(toggleEditOptions);
    $('button.view-area').click(toggleEditOptions);

    $('div.delete-link').click(deleteThis);
    $('a#bulk-edit-show').click(showBulkEdit);
    $('a#bulk-edit-hide').click(hideBulkEdit);
    $('.bulk-edit-item').hover(highlightRow);
    $('.bulk-edit-item').click(selectRow);
    $('a#bulk-edit-select-all').click(selectAll);
    $('a#bulk-edit-select-none').click(selectNone);

    $('#button_set_location').click(setLocation)
    $('#button_clear_location').click(clearLocation)
    $('#button_add_supplements').click(addSupplements)
    $('#button_remove_supplements').click(removeSupplements)

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
    var sall = $('a#bulk-edit-select-all')
    sall.css('display', 'none')
    var snone = $('a#bulk-edit-select-none')
    snone.css('display', 'inline')
    $('.bulk-edit-item').prop('checked', true)
    $.each($('.bulk-edit-item'),turnRowSelectionOn);
    return false;
}
function selectNone(ev) {
    $('a#bulk-edit-select-all').css('display', 'inline')
    $('a#bulk-edit-select-none').css('display', 'none')
    $('.bulk-edit-item').prop('checked', false)
    $.each($('.bulk-edit-item'),turnRowSelectionOff);
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
 }
function turnRowSelectionOn(count, el) {
    var tableRow = $(el.parentElement.parentElement);
    tableRow.toggleClass('select-highlight', true)
}
function turnRowSelectionOff(count, el) {
    var tableRow = $(el.parentElement.parentElement);
    tableRow.toggleClass('select-highlight', false)
}

function showBulkEdit(ev) {
    var el = ev.target;
    $('.bulk-edit-item').css('visibility','visible')
    $('#bulk-edit-select-all').css('display','inline')
    $('#bulk-edit-show').css('display','none')
    $('#bulk-edit-hide').css('display','inline')
    $('.bulk-edit-go').css('visibility','visible')
    return false;
}

function hideBulkEdit(ev) {
    var el = ev.target;
    $('.bulk-edit-item').css('visibility','hidden')
    $('#bulk-edit-show').css('display','inline')
    $('#bulk-edit-hide').css('display','none')
    $('#bulk-edit-select-all').css('display','none')
    $('#bulk-edit-select-none').css('display','none')
    $('.bulk-edit-go').css('visibility','hidden')
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

function setLocation(ev) {
    var newLocationInput = $('input#id_location')
    var newLocation = newLocationInput[0].value
    console.log("setting locs to " + newLocation)
    $('#clear_location')[0].value = 'false'
    let allLocs = $('.area_location')
    allLocs.html(newLocation)
    return false;
}

function clearLocation(ev) {
    $("input#id_location")[0].value = ''
    var clearLoc = $('#clear_location')
    clearLoc[0].value = 'true'
    $('.area_location').html('')
    return false;
}

function addSupplements(ev) {
    // find supplement name/s to add
    var addSupps = $("#id_supplements")
    var newSupps = addSupps.find(":selected")
    // append them to displayed supplements
    $('.area_supp').each(function() {
        var thisObj = $(this)
        newSupps.each( function(count, label) {
            var thisSuppHTML = thisObj.html()
            thisObj.html(thisSuppHTML + ', ' + label.text)
        })

    })
    // store supplement IDs to add on submit
    storeSuppIds('add', newSupps)
    return false;
}

function removeSupplements(ev) {
    var addSupps = $("#id_supplements")
    var newSupps = addSupps.find(":selected")
    $('.area_supp').each(function() {
        var thisObj = $(this)
        newSupps.each( function(count, label) {
            console.log(thisObj)
            console.log(thisObj.html())
            thisObj.html(thisObj.html().replace(label.text, ''))
            thisObj.html(thisObj.html().replace(', , ', ', '))
        })

    })
    // store supplement IDs to remove on submit
    storeSuppIds('remove', newSupps)
    return false;
}

function storeSuppIds(action, selected) {
    var supplist = $("#supp_list_" + action)
    console.log(supplist.val())
    selected.each( function(count, option) {
        supplist.val(supplist.val() + option.value + ':')
    })
}
