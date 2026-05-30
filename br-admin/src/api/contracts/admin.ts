export const ADMIN_NATIVE_META = {
  isReturnNativeResponse: true,
} as const;

export interface AdminPageParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  [key: string]: unknown;
}

export interface AdminPageResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface BasicTableResult<T> {
  list: T[];
  itemCount: number;
  pageCount: number;
  page: number;
}

export function compactQuery<T extends Record<string, unknown>>(params: T): Partial<T> {
  return Object.entries(params).reduce<Partial<T>>((result, [key, value]) => {
    if (value === undefined || value === null || value === '') return result;

    const normalizedValue = typeof value === 'string' ? value.trim() : value;
    if (normalizedValue === '') return result;

    result[key as keyof T] = normalizedValue as T[keyof T];
    return result;
  }, {});
}

export function normalizePageParams<T extends AdminPageParams>(
  params: T = {} as T
): Partial<T> & { page_size?: number } {
  const page_size = params.page_size ?? params.pageSize;
  return compactQuery({
    ...params,
    page_size,
    pageSize: undefined,
  }) as Partial<T> & { page_size?: number };
}

export function toBasicTableResult<T>(response: AdminPageResponse<T>): BasicTableResult<T> {
  return {
    list: response.items,
    itemCount: response.total,
    pageCount: Math.ceil(response.total / response.page_size) || 1,
    page: response.page,
  };
}
