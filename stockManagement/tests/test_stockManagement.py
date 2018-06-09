from flask.ext.testing import TestCase
import stockManagement


class test_stockManagment(TestCase):

    def create_app(self):
        stockapp = stockManagement.app
        stockapp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_item.db'
        return stockapp

    def tearDown(self):
        self.delete_database()

    def test_assert_indexTemplate_used_with_param(self):
        response = self.client.get("/test")
        self.assert_context("name", "test")
        self.assert_template_used('index.html')

    def test_assert_errorTemplate_used(self):
        response = self.client.get("/error")
        self.assert_template_used('error.html')

    def test_assert_listProductsTemplate_used(self):
        self.create_database()
        self.create_product("nail", "A1", 10)
        self.create_product("hammer", "A2", 10)

        response = self.client.get("/product/all")

        self.assert_template_used('list_products.html')
        product = self.get_context_variable("product")
        self.assertEquals(len(product), 2)

        self.delete_database()

    def test_assert_showProductsTemplate_used(self):
        self.create_database()
        self.create_product("nail", "A1", 10)

        response = self.client.get("/product/1")

        self.assert_template_used('show_product.html')
        product = self.get_context_variable("product")
        self.assertEquals(product.name, "nail")

        self.delete_database()

    def test_assert_addProduct_isSecured(self):
        response = self.client.get("/product/add")
        self.assertEquals(True, '<a href="/error">/error</a>' in str(response.data))

    # Setup methods
    def create_database(self):
        stockManagement.db.create_all()

    def create_user_and_role(self):
        stockManagement.user_datastore.create_user(email='oformby', password='password')
        stockManagement.user_datastore.create_role(name='admin', description='admin')
        stockManagement.db.session.commit()

    def add_role_to_user(self):
        stockManagement.user_datastore.add_role_to_user("oformby", "admin")
        stockManagement.db.session.commit()

    def create_product(self, name, allocate, qty):
        me = stockManagement.Item(name, allocate, qty)
        stockManagement.db.session.add(me)
        stockManagement.db.session.commit()

    def delete_database(self):
        stockManagement.db.drop_all()






