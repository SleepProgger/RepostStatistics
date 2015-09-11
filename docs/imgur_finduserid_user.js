// ==UserScript==
// @name        imgur_show_user_id
// @namespace   foo
// @include     http://imgur.com/account/messages
// @version     1
// @grant       none
// ==/UserScript==
// As bookmarklet link: javascript:(function()%7B%24('.message-subject').append(%22%20ID%3A%20%22%20%2B%20%24('.thread-wrapper').attr('data-with-id'))%7D)()

// for messages at load time
$(document).ready(function(){
  $('.date-text').append(" ID: " + $('.thread-wrapper').attr('data-with-id'))  
});

// for dynamically loaded messages
window.observer = new MutationObserver(function(mutations) {
  for(var i=0; i < mutations.length; ++i){
    var mutation = mutations[i];
    for(var j=0; j < mutation.addedNodes.length; ++j){	
      var node = mutation.addedNodes[j];
      if(node.className != "thread-wrapper") continue;
      $('.date-text').append(" ID: " + $('.thread-wrapper').attr('data-with-id'))  
    }
  }
});
var target = document.querySelector('body');
observer.observe(target, { subtree: true, childList: true});