"""empty message

Revision ID: 09a6a03bf366
Revises: 
Create Date: 2024-05-16 12:37:25.224109

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09a6a03bf366'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tb_clientes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=150), nullable=False),
    sa.Column('endereco', sa.String(length=200), nullable=False),
    sa.Column('telefone', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('tb_genero',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tb_usuarios',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=150), nullable=False),
    sa.Column('password', sa.String(length=150), nullable=False),
    sa.Column('e_administrador', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('tb_livro',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('isbn', sa.String(length=13), nullable=False),
    sa.Column('titulo', sa.String(length=200), nullable=False),
    sa.Column('autor', sa.String(length=150), nullable=False),
    sa.Column('genero_id', sa.Integer(), nullable=False),
    sa.Column('qtd_disponivel', sa.Integer(), nullable=False),
    sa.Column('qtd_total', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['genero_id'], ['tb_genero.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('isbn')
    )
    op.create_table('tb_emprestimos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_livro', sa.Integer(), nullable=False),
    sa.Column('id_cliente', sa.Integer(), nullable=False),
    sa.Column('id_usuario', sa.Integer(), nullable=False),
    sa.Column('data_emprestimo', sa.DateTime(), nullable=False),
    sa.Column('data_devolucao', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_cliente'], ['tb_clientes.id'], ),
    sa.ForeignKeyConstraint(['id_livro'], ['tb_livro.id'], ),
    sa.ForeignKeyConstraint(['id_usuario'], ['tb_usuarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tb_emprestimos')
    op.drop_table('tb_livro')
    op.drop_table('tb_usuarios')
    op.drop_table('tb_genero')
    op.drop_table('tb_clientes')
    # ### end Alembic commands ###
