from elasticsearch import NotFoundError
from elasticsearch_dsl import Search, Document, Text, Boolean
from elasticsearch_dsl.connections import connections

connections.create_connection(
    hosts=['127.0.0.1'],
    port=9200,
    use_ssl=False
)


class Article(Document):
    search_word = Text(analyzer="ik_max_word")
    publish_status = Boolean()

    class Index:
        name = 'article'


class SearchByEs:

    def __init__(self):
        Article.init()
        self.article = Article

    def handle_search(self, article_id, search_word, publish_status):
        article = self.article(
            meta={'id': article_id},
            search_word=search_word,
            publish_status=publish_status,
        )
        article.save()

    @staticmethod
    def query_search(search_word, page=1, page_size=10):
        search = Search(
            index='article'
        ).query(
            "match", search_word=search_word
        ).query(
            "match_phrase", publish_status=True
        ).sort(
            '-_id'
        ).source('_id')[(page - 1) * page_size: page * page_size]
        res_count = search.count()
        res = search.execute()

        return res.to_dict(), res_count

    def delete_search(self, article_id):
        try:
            search = self.article.get(id=article_id)
        except NotFoundError:
            return
        else:
            search.delete()
