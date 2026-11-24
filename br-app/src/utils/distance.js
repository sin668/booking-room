const EARTH_RADIUS_METERS = 6371000;

function toNumber(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

/**
 * 计算两个 GCJ-02 坐标之间的球面直线距离（米）。
 * 任一坐标非法时返回 null，调用方应降级展示。
 */
export function haversineDistance(lat1, lng1, lat2, lng2) {
  const latitude1 = toNumber(lat1);
  const longitude1 = toNumber(lng1);
  const latitude2 = toNumber(lat2);
  const longitude2 = toNumber(lng2);
  if (
    latitude1 === null ||
    longitude1 === null ||
    latitude2 === null ||
    longitude2 === null
  ) {
    return null;
  }

  const toRadians = (degrees) => (degrees * Math.PI) / 180;
  const deltaLat = toRadians(latitude2 - latitude1);
  const deltaLng = toRadians(longitude2 - longitude1);
  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(toRadians(latitude1)) *
      Math.cos(toRadians(latitude2)) *
      Math.sin(deltaLng / 2) ** 2;
  return 2 * EARTH_RADIUS_METERS * Math.asin(Math.sqrt(a));
}

/**
 * 格式化距离文案；无效输入返回空字符串，避免展示假数据。
 */
export function formatDistance(meters) {
  const distance = toNumber(meters);
  if (distance === null || distance < 0) {
    return '';
  }
  if (distance < 1000) {
    return `距您约${Math.max(1, Math.round(distance))}m`;
  }
  return `距您约${(distance / 1000).toFixed(1)}km`;
}
