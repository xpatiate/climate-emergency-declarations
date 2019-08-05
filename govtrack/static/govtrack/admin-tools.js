"use strict";

var showing = {};
$( document ).ready(function() {
    $( "button.view-nodetype" ).click( toggleEditOptions );
    $( "button.view-node" ).click( toggleEditOptions );
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

/* 
Process for multiple node creation:

User clicks "quick add multiple" link, which fires showMultiAddForm()
  -> Display form containing textarea with action specifying IDs
  -> Attach paste event listener to textarea
User pastes HTML into textarea, which fires getPastedHTML()
  -> Extract HTML from clipboard data, or plain text if there is no HTML
  -> If HTML contains a table
    -> Send HTML to API to extract nodes
    -> If API returns a good response, replace textarea contents with API response
User clicks 'create' button, form submits - no JS nivolved
  -> Submit form to API which parses textarea data and creates nodes
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
        var dom_nodes = $($.parseHTML(pastedText))
        var table_node = dom_nodes.closest('table');
        if (table_node.length) {
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

    // After HTML text is pasted, send it to the API to extract the nodes and URLs
    // Replace the textarea contents with the API response
    function extractPastedData(target) {
        var pastedText = target.html()
        jQuery.ajax('/cegov/api/extract_nodes', {
            'method': 'POST',
            'data': {
                'node_table': pastedText,
            },
            'success': function(response) {
                target.html(response['nodes'])
            }
        });
    }
