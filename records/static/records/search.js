const search = document.querySelector("#search-input");
const result = document.querySelector("#search-results");
const status = document.querySelector("#search-status");
let timer;
let request;

search.addEventListener("input", () => {
    clearTimeout(timer);
    request?.abort();
    timer = setTimeout(async () => {
        request = new AbortController();
        const params = new URLSearchParams({q: search.value});
        try {
            const response = await fetch(search.dataset.url + "?" + params, {signal: request.signal});
            if (!response.ok) throw new Error("Ошибка поиска");
            result.innerHTML = await response.text();
            status.textContent = "";
        } catch (error) {
            if (error.name !== "AbortError") status.textContent = "Поиск недоступен. Попробуйте снова.";
        }
    }, 200);
});
