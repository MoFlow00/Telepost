export default {

  async fetch(request) {

    const url = new URL(request.url)

    const channel =
    url.searchParams.get("channel")

    if(!channel){

      return new Response(
        "Missing channel",
        { status: 400 }
      )

    }

    const telegramUrl =
    `https://t.me/s/${channel}`

    const response =
    await fetch(telegramUrl, {

      headers: {
        "User-Agent":
        "Mozilla/5.0"
      }

    })

    let html =
    await response.text()

    html = html.replaceAll(
      'https://telegram.org/',
      'https://telegram.org/'
    )

    return new Response(html, {

      headers: {
        "Content-Type":
        "text/html;charset=UTF-8",

        "Access-Control-Allow-Origin":
        "*"
      }

    })

  }

}
