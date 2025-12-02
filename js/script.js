//var socket = io();
//io.connect('http://localhost:5000');

var socket = io.connect("http://localhost:5000");

var zachImage = document.getElementById("zach-image");
var clickCount = 0;
var lockImage = false;
var navPopulated = false;


checkScrollPosition();
$("#nav-on-scroll").addClass("nav-top-hidden");
            $("#nav-on-scroll").removeClass("nav-top-visible")
         
            function socketTest()
            {

            }


            const currentUrl = window.location.href;
            console.log(currentUrl);
            if (currentUrl.toLowerCase().includes('?lovegame')) {
               console.log("REDIRECT");
                window.location.href = 'lovegame.html';
            }

$(window).scroll(function() {
    var scrollY = $(window).scrollTop();
    if(scrollY >= 200) {
      if(!navPopulated)
      {
        //Show NavBar on scroll 
        $("#nav-on-scroll").removeClass("nav-top-hidden");
        $("#nav-on-scroll").addClass("nav-top-visible")
        navPopulated = true;
      }
    }
    else if(scrollY)
    {
        if(navPopulated)
        {
            console.log("Hide Nav");
            $("#nav-on-scroll").addClass("nav-top-hidden");
            $("#nav-on-scroll").removeClass("nav-top-visible")
            navPopulated = false;
        }
    }
  });


  function projectPaused()
  {
    swal("This project is paused!", "This project is currently paused due to other priorities, but I have plans to bring it back, and likely will make it free to offer a nice collaboration tool to whoever wants it.", "info");
  }


  function projectComingSoon()
  {
    swal("This project is coming soon!", "This game is currently in development, and will be available soon. Feel free to send me an email if you'd like to be notified when it's released.", "info");
  }

  function projectRetired()
  {
    swal("This project is retired!", "Unfortunately, this project is no longer available. Don't worry, it may come back some day. In the meantime, why not check out some of my other projects?", "info");
  }

  function showUnderDevelopment(serviceName)
  {
    swal({
      title: "Under Development",
      text: "The " + serviceName + " portfolio page is currently under development. If you would like to see more of my work in this area, please contact me directly and I'll be happy to share more details.",
      icon: "info",
      buttons: {
        cancel: "Close",
        contact: {
          text: "Contact Me",
          value: "contact",
        },
      },
    }).then((value) => {
      if (value === "contact") {
        toggleContactMe('show');
      }
    });
  }

  function socketTest()
  {
    console.log("SOCKET TEST");
    console.log(socket);
    socket.emit('remote-action', {socketActionType: "socketTestingAction", userPlatform: "mobile"});
}

  
function openMobileNav()
{
    $("#mobile-nav").removeClass("offscreen-nav-hidden");
    document.body.style.overflow = 'hidden';
}

function closeMobileNav()
{
    $("#mobile-nav").addClass("offscreen-nav-hidden");
    document.body.style.overflow = 'initial';
}

function checkScrollPosition()
{
    var currentURL = window.location.href;
    currentURL = currentURL.split("#")[1];
    if(currentURL == "contact") {
        toggleContactMe('show');
    }

    var scrollY = $(window).scrollTop();
    if(scrollY >= 200) {
      if(!navPopulated)
      {
        //Show NavBar on scroll 
        console.log("Populate nav!");
        $("#nav-on-scroll").removeClass("nav-top-hidden");
        $("#nav-on-scroll").addClass("nav-top-visible")
        navPopulated = true;
      }
    }
    else if(scrollY)
    {
        if(navPopulated)
        {
            console.log("Hide Nav");
            $("#nav-on-scroll").addClass("nav-top-hidden");
            $("#nav-on-scroll").removeClass("nav-top-visible")
            navPopulated = false;
        }
    }
}

function openContact()
{
    closeMobileNav();
    toggleContactMe("show");
}

function toggleContactMe(action)
{
    if(action == "show")
    {
        $("#contact-me-pane").removeClass("contact-me-inactive");
        $("#contact-me-pane").addClass("contact-me-active");
    }
    else if(action == "hide")
    {
        $("#contact-me-pane").addClass("contact-me-inactive");
        $("#contact-me-pane").removeClass("contact-me-active");
    }
}

function zachShades()
{
    if(!lockImage)
    {
        zachImage.src = "img/zach-shades.png";
    }
}

function scrollToSection(section)
{   
    var elmnt = document.getElementById(section);
    elmnt.scrollIntoView();
    closeMobileNav();
}

function zachNormal()
{
    if(!lockImage)
    {
        zachImage.src = "img/zach.png";
    }
}

function iterateClickCount(){clickCount++;if(clickCount==1){zachShades();} if(clickCount == 420){zachImage.src = "img/zach-shades-stupid-secret.png"; lockImage = true;}}