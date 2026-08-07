let viewer;

let currentBook;

let currentPage = 1;

let maxPage = 9999;

let searchIndex = [];

function getBook() {

    const params =
        new URLSearchParams(
            location.search
        );

    return (
        params.get("book")
        || "l4d2"
    );
}

currentBook = getBook();

const BOOKS_ORIGIN =
    "https://assets.dakang233.com";

if (!/^[a-zA-Z0-9_-]+$/.test(currentBook)) {
    throw new Error("无效的书籍标识");
}

const basePath =
    `${BOOKS_ORIGIN}/books/${currentBook}/`;

function pagePath(page) {

    const p =
        String(page)
        .padStart(3,"0");

    return (
        `${basePath}page${p}.dzi`
    );
}

viewer = OpenSeadragon({
    id: "viewer",
    prefixUrl: "/openseadragon/images/",
    tileSources: pagePath(1),

    crossOriginPolicy: "Anonymous",
    ajaxWithCredentials: false,

    gestureSettingsTouch: {
        pinchToZoom: true,      // 支持双指缩放
        flickEnabled: true,     // 惯性滚动
        clickToZoom: false,     // 单指点击不放大
        dblClickToZoom: false   // 双击不放大
    }
});

function openPage(page){

    if (page > maxPage) {
        alert("输入的页数超过最大页数:" + maxPage);
        return;
    }

    currentPage = page;

    viewer.open(
        pagePath(page)
    );

    document
    .getElementById("pageInfo")
    .textContent =
        `第 ${page} 页`;

    document
    .getElementById("pageInput")
    .value =
        page;

    localStorage.setItem(
        currentBook,
        page
    );
}

const lastPage =
    localStorage.getItem(
        currentBook
    );

if(lastPage){

    setTimeout(()=>{

        openPage(
            Number(lastPage)
        );

    },500);

}

fetch(
    basePath +
    "book_toc.json"
)
.then(r=>r.json())
.then(toc=>{

    const ul =
        document
        .getElementById("toc");

    toc.forEach(item=>{

        const li =
            document
            .createElement("li");

        li.textContent =
            item.title;

        li.onclick = () => {
            openPage(
                item.page
            );
            // 手机端点击书签后自动收起目录
            if(window.innerWidth <= 768){
                sidebar.classList.remove("show");
            }
        }

        ul.appendChild(li);

    });

});

fetch(
    basePath +
    "search_index.json"
)
.then(r=>r.json())
.then(data=>{

    searchIndex = data;

});

document
.getElementById("searchBtn")
.onclick = ()=>{

    const keyword =
        document
        .getElementById(
            "searchInput"
        )
        .value;

    const result =
        searchIndex.filter(
            x=>
            x.text &&
            x.text.includes(
                keyword
            )
        );

    if(result){

        openPage(
            result.page
        );

    }
    };


document
.getElementById("prevPage")
.onclick = ()=>{

    if(currentPage > 1){

        openPage(
            currentPage - 1
        );

    }

};

document
.getElementById("nextPage")
.onclick = ()=>{

    openPage(
        currentPage + 1
    );

    };

document
.getElementById("goPage")
.onclick = ()=>{

    const page =
        Number(
            document
            .getElementById(
                "pageInput"
            )
            .value
        );

    if(page > 0){

        openPage(page);

    }

    };

fetch(
    `${basePath}metadata.json?t=${Date.now()}`
)
.then(r=>r.json())
.then(meta=>{

    document.title =
        meta.title;

    maxPage =
        meta.pages;
    
    document
    .getElementById("version")
    .textContent =
        `当前版本：${meta.version}`;

    document
    .getElementById("lastUpdateTime")
    .textContent =
        `最后更新时间：${meta.lastUpdateTime}`;
    document
        .getElementById("author")
        .textContent = `作者：${meta.author}`;
});

const sidebar = document.getElementById("sidebar");
const menuBtn = document.getElementById("menuBtn");

menuBtn.onclick = () => {
    sidebar.classList.toggle("show");
};


let startX = 0;

viewer.addHandler("canvas-touch-start", function(event) {
    if(event.touches && event.touches.length === 1){
        startX = event.touches[0].clientX;
    }
});

viewer.addHandler("canvas-touch-end", function(event) {
    if(event.changedTouches && event.changedTouches.length === 1){
        let endX = event.changedTouches[0].clientX;
        let delta = endX - startX;

        if(delta > 50){
            // 向右滑
            openPage(Math.max(currentPage - 1, 1));
        } else if(delta < -50){
            // 向左滑
            openPage(currentPage + 1);
        }
    }
});