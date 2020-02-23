'use strict';

var showing = {};
$(document).ready(() => {
    $('button.view-structure').click(toggleEditOptions);
    $('button.view-area').click(toggleEditOptions);
    $('a#do_update_popcount').click(triggerRecount);
    $('a#update_all_popcounts').click(triggerAllRecounts);

    $('div.delete-link').click(deleteThis);
    $('a#bulk-edit-show').click(showBulkEdit);
    $('a#bulk-edit-hide').click(hideBulkEdit);
    $('.bulk-edit-item').hover(highlightRow);
    $('.bulk-edit-item').click(selectRow);
    $('a#bulk-edit-select-all').click(selectAll);
    $('a#bulk-edit-select-none').click(selectNone);
    $('a.setup-clone').click(setupClone);
    $('#cancel-clone').click(cancelClone);
    $('.clone-parent-item').hover(highlightRow);
    $('.clone-parent-item').click(selectRow);

    $('#button_set_location').click(setLocation)
    $('#button_clear_location').click(clearLocation)
    $('#button_set_link').click(setLink)
    $('#button_undo_link').click(undoLink)
    $('#button_add_supplements').click(addSupplements)
    $('#button_remove_supplements').click(removeSupplements)
    $('#bulk_delete_button').click(confirmBulkDelete)
    $('#bulk_edit_button').click(submitBulkEdit)
    window.supplementNames = {}
    parseSuppNames()

    let toggleInboxEl = $('.toggle-inbox');
    
    if (toggleInboxEl.length > 0) {
        if (localStorage.getItem('inbox') == 'hidden') {
            toggleInbox();
        }
        
        toggleInboxEl.click(toggleInbox);
    }
    
    $('.inbox-paste textarea').bind('paste', pasteInbox);
});

function setupClone(ev) {
    var cloneSrc = ev.target
    cancelClone()
    var cloneRow = $(cloneSrc).parents('.structure-row')
    cloneRow.addClass('clone-src')
    var cloneId = cloneSrc.dataset.id
    var cloneName = cloneSrc.dataset.name
    $('#clone-src-name').html(cloneName)
    $('.clone-action').css('display','block')
    $('.clone-parent-item').each(function(count, item) {
      if (item.value != cloneId) {
        $(item).css('visibility','visible')
      }
    });
    $('#clone-src-id').val(cloneId)
    return false;
}
function cancelClone(ev) {
    $('.structure-row').removeClass('clone-src')
    $('.clone-action').css('display','none')
    $('.clone-parent-item').css('visibility','hidden')
    $('.clone-parent-item').prop('checked', false)
    $.each($('.clone-parent-item'),turnRowSelectionOff);
    $('#clone-src-name').html('')
    $('#clone-src-id').val(0)
}

function confirmBulkDelete(ev) {
    var numChecked = collectBulkEditAreas()
    if (numChecked > 0) {
        var confStr = 'Are you sure you want to delete ' 
        if (numChecked == 1) {
            confStr += 'this area and any dependents'
        }
        else {
            confStr += 'these ' + numChecked + ' areas and their dependents'
        }
        confStr += '? This cannot be undone.'
        const response = confirm(confStr)
        if (response == true) {
          $('#bulk_edit_action').val('delete')
          $('#bulk_edit_form').submit()
        }
    }
    return false
}

function submitBulkEdit(ev) {
  // get all checked checkboxes, add to a hidden field
    var numChecked = collectBulkEditAreas()
    if (numChecked > 0) {
          $('#bulk_edit_action').val('edit')
          $('#bulk_edit_form').submit()
    }
    return false
}

function collectBulkEditAreas() {
    var checkBoxes = $("input[name='bulk-areas']:checked")
    var idlist = []
    checkBoxes.each(function(count, box) {
      idlist.push(box.value)
    });
    $('#bulk_area_id_str').val(idlist.join(':'))
    return idlist.length
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
                    window.location.href = window.location.href;
                } else {
                    alert("operation failed");
                }
            }
        }
        oReq.open("GET", apiUrl);
        oReq.send();
    }
}

function triggerAllRecounts(ev) {
    ev.preventDefault()
    var el = ev.target;
    var apiUrl = el.dataset.url
    console.log('making API call to ' + apiUrl);
    var oReq = new XMLHttpRequest();
    oReq.onreadystatechange = () => {
        if (oReq.readyState === 4) {
            console.log(oReq);
            if (oReq.status != '200') {
                alert("operation failed");
            }
        }
    }
    oReq.open("GET", apiUrl);
    oReq.send();
    $(el).html('')
    $('.update-needed').html('')
};

function triggerRecount(ev) {
    ev.preventDefault()
    var el = ev.target;
    var parentDiv = el.parentElement;
    var apiUrl = el.dataset.url
    console.log('making API call to ' + apiUrl);
    var oReq = new XMLHttpRequest();
    oReq.onreadystatechange = () => {
        if (oReq.readyState === 4) {
            console.log(oReq);
            if (oReq.status != '200') {
                alert("operation failed");
            }
        }
    }
    oReq.open("GET", apiUrl);
    oReq.send();
    $('.popcount-status').html('popcount running...')
    $('.popcount-status').addClass('popcount-running')
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
            let rowLinks = [];
            for (let cell = 0; cell < table.children[row].children.length; cell++) {
                let thisCell = table.children[row].children[cell];
                if (split_links) {
                    let link = thisCell.querySelector('a');
                    if (link) {
                        let linkText = link.textContent;
                        let linkTarget = link.getAttribute('href');
                        if (linkText != linkTarget) {
                            values[row].push(link.textContent);
                        }
                        rowLinks.push(linkTarget);
                    } else {
                        values[row].push(thisCell.textContent);
                    }
                } else {
                    values[row].push(thisCell.textContent);
                }
            }
            rowLinks.forEach(function(link){
              values[row].push(link);
            });
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
    var etypes = ['form', 'text']
    $.each( etypes, function(count, thing) {
        var target = $( '#' + thing + '_' +  target_id);
        if (target.css('display') != 'inline') {
            target.css('display', 'inline');
            target.on('paste', getPastedHTML);
        } else {
            target.css('display', 'none');
            target.off('paste', getPastedHTML);
        }
    });
    return false;
}

/* BULK AREA EDIT FUNCTIONS */

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
    $('.bulk-edit-item').css('visibility','visible')
    $('#bulk-edit-select-all').css('display','inline')
    $('#bulk-edit-show').css('display','none')
    $('#bulk-edit-hide').css('display','inline')
    $('.bulk-edit-go').css('visibility','visible')
    return false;
}

function hideBulkEdit(ev) {
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

function setLocation(ev) {
    var newLocationInput = $('input#id_location')
    var newLocation = newLocationInput[0].value
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

function setLink(ev) {
    var newLinkInput = $('input#id_link')
    var newLink = newLinkInput[0].value
    let allLocs = $('.area_link')
    allLocs.html(newLink)
    allLocs.prop('title', newLink)
    $('#do_set_link').val('true')
    return false;
}

function undoLink(ev) {
    var newLinkInput = $('input#id_link')
    newLinkInput[0].value = ''
    let allLocs = $('.area_link')
    allLocs.html('')
    allLocs.prop('title', '')
    $('#do_set_link').val('false')
    return false;
}

// add selected areas as supplementary parents
function addSupplements(ev) {
    var addSupps = $("#id_supplements_add")
    var newSupps = addSupps.find(":selected")
    storeSuppIds('add', newSupps, 'rm')
    // add this option to the 'to-remove' select menu
    var rmSupp = $("#id_supplements_rm")
    var existingOpts = $("#id_supplements_rm option").map(function() { return $(this).val(); }).get();
    newSupps.each( function(count, adding) {
        if (!isInArray(adding.value, existingOpts)) {
            rmSupp.append(new Option(adding.text, adding.value))
        }
    })
    $("#id_supplements_add option:selected").prop('selected' , false)
    sortSelects()
    return false
}

// remove selected areas as supplementary parents
function removeSupplements(ev) {
    var rmSupps = $("#id_supplements_rm")
    var newSupps = rmSupps.find(":selected")
    storeSuppIds('rm', newSupps, 'add')
    $("#id_supplements_rm option:selected").remove()
    sortSelects()
    return false
}

// sort the options in both select menus
function sortSelects() {
    ['#id_supplements_add', '#id_supplements_rm'].forEach(
        function(selectId) {
        var options = $(selectId + " option");   // Collect options
        options.detach().sort(function(a,b) {    // Detach from select, then Sort
            var at = $(a).text();
            var bt = $(b).text();
            return (at > bt)?1:((at < bt)?-1:0); // Do the sort
        });
        options.appendTo(selectId);
        }
    );
}
// update the displayed list of supplementary parent names
function redrawSuppNames( actionLists ) {
    var newSupps = []
    var suppNames = window.supplementNames
    //var addHolder = $("#supp_list_add")[0]
    //var ids_to_add = readIds(addHolder.value)
    var ids_to_add = actionLists['add']
    //var rmHolder = $("#supp_list_rm")[0]
    //var ids_to_rm = readIds(rmHolder.value)
    var ids_to_rm = actionLists['rm']
    $('.area_supp').each(function() {
        var thisObj = $(this)
        var name_list = thisObj.html().split(', ')

        ids_to_add.forEach( function(s_id) {
            var this_name = suppNames[s_id]
            if (!isInArray(this_name, name_list)) {
                name_list.push(this_name)
            }
        })

        ids_to_rm.forEach( function(s_id) {
            var this_name = suppNames[s_id]
            if (isInArray(this_name, name_list)) {
                var new_list = name_list.filter(function(name) {
                    return name != this_name
                })
                name_list = new_list
            }
        })
        var sortedNames = $.grep(name_list, function(e) {
            return e.length > 0
            }).sort()
        thisObj.html(sortedNames.join(', '))
        thisObj.prop('title',sortedNames.join(', '))
    })
}

// add selected options to the appropriate add/remove hidden field,
// and remove from the other one
function storeSuppIds(action, selected, opposite) {
    var supplist = $("#supp_list_" + action)
    var idlist = readIds(supplist.val())
    selected.each( function(count, option) {
        // add ids to the selection action list
        if (!isInArray(option.value, idlist)) {
            idlist.push(option.value)
        }
    })
    supplist.val(serialiseIds(idlist))
    // and remove ID from the opposite action list
    var opplist = $("#supp_list_" + opposite)
    var oppIdList = readIds(opplist.val())
    var newList = oppIdList.filter(function(oppId) {
        return !isInArray(oppId, idlist)
    })
    opplist.val(serialiseIds(newList))
    var actionLists = {}
    actionLists[action] = idlist
    actionLists[opposite] = newList
    redrawSuppNames( actionLists )
}

// turn a list of ids into a serialised string
function serialiseIds(idlist) {
    var unique_ids = []
    $.each(idlist, function(i, e) {
        if (!isInArray(e, unique_ids)) unique_ids.push(e);
    });
    return unique_ids.join(':')
}

// turn a serialised string of ids into a list
function readIds(idstr) {
    if (idstr.length) {
        var idlist = idstr.split(':')
        var idsWithValues = $.grep(idlist, function(e) { 
            return e.length > 0
            })
        return idsWithValues
    }
    return []
}

// read options from the supplementary parents menus and make a lookup hash
function parseSuppNames() {
    var suppnames = window.supplementNames
    var elements = ["#id_supplements_add", "#id_supplements_rm"]
    elements.forEach( function(el) {
        var options = $(el + " option")
        var values = $.map(options, function(option) {
            suppnames[option.value] = option.text
        })
    })
}

function isInArray(value, valList) {
    return $.inArray(value, valList) > -1
}

/* END BULK AREA EDIT */
