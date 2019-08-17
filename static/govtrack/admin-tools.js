"use strict";

var showing = {};
$( document ).ready(function() {
    $( "button.view-structure" ).click( toggleEditOptions );
    $( "button.view-area" ).click( toggleEditOptions );

    $('div.delete-link').click( deleteThis );
});

function toggleEditOptions(ev) {
    var el = ev.target
    var editdivid = el.id.replace('view','edit')
    var editdiv = $( '#' + editdivid )
    if (showing[el.id] == 1) {
        editdiv.css('display','none')
        showing[el.id] = 0
        el.innerHTML = '*'
    } else {
        editdiv.css('display','block')
        showing[el.id] = 1
        el.innerHTML = '-'
    }
}

function deleteThis(ev) {
    ev.preventDefault()
    var el = ev.target;
    var parentDiv = el.parentElement;
    var apiUrl = parentDiv.dataset.url;
    var objType = parentDiv.dataset.type;
    var objectId = objType + '-' + parentDiv.dataset.id;
    const response = confirm('Are you sure you want to delete this ' + objType + '?');
    if (response) {
        var mainObj = $('#' + objectId)
        mainObj.css('display','none');
        console.log('making API call to ' + apiUrl);
        //TODO make this a POST with CSRF
        var oReq = new XMLHttpRequest();
        oReq.open("GET", apiUrl);
        oReq.send();
    }
};

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
        var target = $( '#' + target_id)
        target.css('display', 'inline')
        target.on('paste', getPastedHTML );
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
