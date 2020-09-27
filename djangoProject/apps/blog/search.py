import datetime
from elasticsearch_dsl import Search, Document, Text, Boolean, Date, Keyword, UpdateByQuery
from elasticsearch_dsl.connections import connections

connections.create_connection(
    hosts=['127.0.0.1'],
    port=9200,
    use_ssl=False
)
article_index = "article8"


class Article(Document):
    search_word = Text(analyzer="ik_max_word")
    author = Text(fields={'raw': Keyword()})
    datetime_created = Date()
    publish_status = Boolean()

    class Index:
        name = article_index

    def save(self, **kwargs):
        self.datetime_created = datetime.datetime.now()
        return super().save(**kwargs)


class SearchByEs:

    def __init__(self):
        Article.init()
        self.article = Article

    def handle_search(self, article_id, search_word, publish_status, author):
        article = self.article(
            meta={'id': article_id},
            author=author,
            search_word=search_word,
            publish_status=publish_status,
        )
        article.save()

    @staticmethod
    def update_search_by_author(old_author, new_author):
        ubq = UpdateByQuery(index=article_index).query(
            "match_phrase", author=old_author
        ).script(
            source="ctx._source.author = params.author",
            lang='painless',
            params={
                'author': new_author
            }
        )
        ubq.execute()

    @staticmethod
    def query_search(search_word, page=1, page_size=10):
        search = Search(
            index=article_index
        ).query(
            "multi_match", query=search_word, fields=['author', 'search_word']
        ).query(
            "match_phrase", publish_status=True
        ).sort(
            '-datetime_created'
        ).source(
            '_id'
        )[(page - 1) * page_size: page * page_size]
        res_count = search.count()
        res = search.execute()

        return res.to_dict(), res_count

    def delete_search(self, article_id):
        search = self.article.get(id=article_id, ignore=404)
        if search is not None:
            search.delete()
