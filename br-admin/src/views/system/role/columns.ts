import { h } from 'vue';
import { NTag } from 'naive-ui';

export const columns = [
  {
    title: 'ID',
    key: 'id',
  },
  {
    title: '角色名称',
    key: 'name',
  },
  {
    title: '角色编码',
    key: 'code',
  },
  {
    title: '说明',
    key: 'description',
  },
  {
    title: '状态',
    key: 'status',
    render(row) {
      return h(
        NTag,
        {
          type: row.status === 'active' ? 'success' : 'error',
        },
        {
          default: () => (row.status === 'active' ? '启用' : '禁用'),
        }
      );
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
  },
];
