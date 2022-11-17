/* Click the body of an element to go to story */
const click_story = (story_id) => {
    window.location.replace(`/story/${story_id}`);
};

/* Function for triggering visual updates*/
const toggle_refresh = () => {
    refresh_icon = document.getElementById("refresh_icon");
    if (refresh_icon.style.display === "none") refresh_icon.style.display = "";
    else refresh_icon.style.display = "none";
};

/* Returns bool of if login is required */
const get_login_required = (res) => {
    params = new URL(res.url).searchParams;
    url_params = new URLSearchParams(params);
    return url_params.get("login_required");
};

/* Toggle story like */
const toggle_like = (element, story_id) => {
    let url = `/story/${story_id}/like`;

    /* Toggle like button if story is disliked already */
    const dislike_button = element.parentElement.querySelector("#dislike");
    if (dislike_button.classList.contains("disliked")) {
        toggle_dislike(dislike_button, story_id);
    }

    /* If element is liked already, unlike it */
    if (element.classList.contains("liked")) {
        element.classList.remove("liked");
        element.classList.remove("bi-caret-up-fill");
        element.classList.add("bi-caret-up");
        url += "/remove";
    } else {
        element.classList.add("liked");
        element.classList.remove("bi-caret-up");
        element.classList.add("bi-caret-up-fill");
        url += "/add";
    }

    fetch(url).then((res) => {
        if (get_login_required(res)) {
            window.location.replace(res.url);
        }
    });
};

/* Toggle story dislike */
const toggle_dislike = (element, story_id) => {
    let url = `/story/${story_id}/dislike`;

    /* Toggle like button if story is liked already */
    const like_button = element.parentElement.querySelector("#like");
    if (like_button.classList.contains("liked")) {
        toggle_like(like_button, story_id);
    }

    /* If element is disliked already, undislike it */
    if (element.classList.contains("disliked")) {
        element.classList.remove("disliked");
        element.classList.remove("bi-caret-down-fill");
        element.classList.add("bi-caret-down");
        url += "/remove";
    } else {
        element.classList.add("disliked");
        element.classList.remove("bi-caret-down");
        element.classList.add("bi-caret-down-fill");
        url += "/add";
    }

    fetch(url).then((res) => {
        if (get_login_required(res)) {
            window.location.replace(res.url);
        }
    });
};

const hover_like = (element) => {
    element.classList.remove("bi-caret-up");
    element.classList.add("bi-caret-up-fill");
};

const unhover_like = (element) => {
    if (!element.classList.contains("liked")) {
        element.classList.remove("bi-caret-up-fill");
        element.classList.add("bi-caret-up");
    }
};

const hover_dislike = (element) => {
    element.classList.remove("bi-caret-down");
    element.classList.add("bi-caret-down-fill");
};

const unhover_dislike = (element) => {
    if (!element.classList.contains("disliked")) {
        element.classList.remove("bi-caret-down-fill");
        element.classList.add("bi-caret-down");
    }
};

/* Update comments */
const update_comments = async (element) => {
    toggle_refresh();
    await fetch("/update/comments").then((res) =>
        res.json().then((data) => {
            display_update_comments_time(data.time_taken);
            toggle_refresh();
        })
    );
};

/* Display time it took to update comments */
const display_update_comments_time = (time) => {
    update_comments_time = document.getElementById("update_comments_time");
    update_comments_time_block = document.getElementById(
        "update_comments_time_block"
    );

    update_comments_time_block.style.display = "";
    update_comments_time.textContent = time;
};
