const EC_LEVEL_L = 1

const RS_BLOCKS_L = {
  1: [[1, 26, 19]],
  2: [[1, 44, 34]],
  3: [[1, 70, 55]],
  4: [[1, 100, 80]],
  5: [[1, 134, 108]],
  6: [[2, 86, 68]],
  7: [[2, 98, 78]],
  8: [[2, 121, 97]],
  9: [[2, 146, 116]],
  10: [[2, 86, 68], [2, 87, 69]],
  11: [[4, 101, 81]],
  12: [[2, 116, 92], [2, 117, 93]],
  13: [[4, 133, 107]],
  14: [[3, 145, 115], [1, 146, 116]],
  15: [[5, 109, 87], [1, 110, 88]],
  16: [[5, 122, 98], [1, 123, 99]],
  17: [[1, 135, 107], [5, 136, 108]],
  18: [[5, 150, 120], [1, 151, 121]],
  19: [[3, 141, 113], [4, 142, 114]],
  20: [[3, 135, 107], [5, 136, 108]],
}

const ALIGNMENT_POSITIONS = {
  1: [],
  2: [6, 18],
  3: [6, 22],
  4: [6, 26],
  5: [6, 30],
  6: [6, 34],
  7: [6, 22, 38],
  8: [6, 24, 42],
  9: [6, 26, 46],
  10: [6, 28, 50],
  11: [6, 30, 54],
  12: [6, 32, 58],
  13: [6, 34, 62],
  14: [6, 26, 46, 66],
  15: [6, 26, 48, 70],
  16: [6, 26, 50, 74],
  17: [6, 30, 54, 78],
  18: [6, 30, 56, 82],
  19: [6, 30, 58, 86],
  20: [6, 34, 62, 90],
}

const EXP_TABLE = new Array(512)
const LOG_TABLE = new Array(256)

let x = 1
for (let i = 0; i < 255; i++) {
  EXP_TABLE[i] = x
  LOG_TABLE[x] = i
  x <<= 1
  if (x & 0x100) x ^= 0x11d
}
for (let i = 255; i < 512; i++) {
  EXP_TABLE[i] = EXP_TABLE[i - 255]
}

function gfMul(a, b) {
  if (a === 0 || b === 0) return 0
  return EXP_TABLE[LOG_TABLE[a] + LOG_TABLE[b]]
}

function polyMul(a, b) {
  const result = new Array(a.length + b.length - 1).fill(0)
  for (let i = 0; i < a.length; i++) {
    for (let j = 0; j < b.length; j++) {
      result[i + j] ^= gfMul(a[i], b[j])
    }
  }
  return result
}

function rsGenerator(degree) {
  let poly = [1]
  for (let i = 0; i < degree; i++) {
    poly = polyMul(poly, [1, EXP_TABLE[i]])
  }
  return poly
}

function rsRemainder(data, degree) {
  const generator = rsGenerator(degree)
  const result = data.concat(new Array(degree).fill(0))
  for (let i = 0; i < data.length; i++) {
    const factor = result[i]
    if (factor === 0) continue
    for (let j = 0; j < generator.length; j++) {
      result[i + j] ^= gfMul(generator[j], factor)
    }
  }
  return result.slice(result.length - degree)
}

function utf8Bytes(text) {
  if (typeof TextEncoder !== 'undefined') {
    return Array.from(new TextEncoder().encode(text))
  }

  const bytes = []
  const encoded = encodeURIComponent(text)
  for (let i = 0; i < encoded.length; i++) {
    if (encoded[i] === '%') {
      bytes.push(parseInt(encoded.slice(i + 1, i + 3), 16))
      i += 2
    } else {
      bytes.push(encoded.charCodeAt(i))
    }
  }
  return bytes
}

function getBlocks(version) {
  const blockDefs = RS_BLOCKS_L[version]
  if (!blockDefs) throw new Error('QR version is not supported')

  const blocks = []
  for (const [count, totalCodewords, dataCodewords] of blockDefs) {
    for (let i = 0; i < count; i++) {
      blocks.push({ totalCodewords, dataCodewords, ecCodewords: totalCodewords - dataCodewords })
    }
  }
  return blocks
}

function totalDataCodewords(version) {
  return getBlocks(version).reduce((sum, block) => sum + block.dataCodewords, 0)
}

function chooseVersion(byteLength) {
  for (let version = 1; version <= 20; version++) {
    const lengthBits = version < 10 ? 8 : 16
    const requiredBits = 4 + lengthBits + byteLength * 8
    if (requiredBits <= totalDataCodewords(version) * 8) return version
  }
  throw new Error('QR content is too long')
}

function appendBits(bits, value, length) {
  for (let i = length - 1; i >= 0; i--) {
    bits.push((value >>> i) & 1)
  }
}

function createDataCodewords(bytes, version) {
  const capacity = totalDataCodewords(version)
  const bits = []
  appendBits(bits, 0x4, 4)
  appendBits(bits, bytes.length, version < 10 ? 8 : 16)
  for (const byte of bytes) appendBits(bits, byte, 8)

  const maxBits = capacity * 8
  appendBits(bits, 0, Math.min(4, maxBits - bits.length))
  while (bits.length % 8) bits.push(0)

  const codewords = []
  for (let i = 0; i < bits.length; i += 8) {
    let value = 0
    for (let j = 0; j < 8; j++) value = (value << 1) | bits[i + j]
    codewords.push(value)
  }

  let pad = 0xec
  while (codewords.length < capacity) {
    codewords.push(pad)
    pad = pad === 0xec ? 0x11 : 0xec
  }
  return codewords
}

function createCodewords(dataCodewords, version) {
  const blocks = getBlocks(version)
  const dataBlocks = []
  const ecBlocks = []
  let offset = 0

  for (const block of blocks) {
    const data = dataCodewords.slice(offset, offset + block.dataCodewords)
    offset += block.dataCodewords
    dataBlocks.push(data)
    ecBlocks.push(rsRemainder(data, block.ecCodewords))
  }

  const result = []
  const maxDataLength = Math.max(...dataBlocks.map((block) => block.length))
  for (let i = 0; i < maxDataLength; i++) {
    for (const block of dataBlocks) {
      if (i < block.length) result.push(block[i])
    }
  }

  const maxEcLength = Math.max(...ecBlocks.map((block) => block.length))
  for (let i = 0; i < maxEcLength; i++) {
    for (const block of ecBlocks) {
      if (i < block.length) result.push(block[i])
    }
  }
  return result
}

function makeMatrix(size) {
  return {
    modules: Array.from({ length: size }, () => new Array(size).fill(false)),
    reserved: Array.from({ length: size }, () => new Array(size).fill(false)),
  }
}

function setModule(matrix, row, col, dark, reserved = true) {
  if (row < 0 || col < 0 || row >= matrix.modules.length || col >= matrix.modules.length) return
  matrix.modules[row][col] = !!dark
  if (reserved) matrix.reserved[row][col] = true
}

function drawFinder(matrix, row, col) {
  for (let r = -1; r <= 7; r++) {
    for (let c = -1; c <= 7; c++) {
      const rr = row + r
      const cc = col + c
      const dark = r >= 0 && r <= 6 && c >= 0 && c <= 6 && (r === 0 || r === 6 || c === 0 || c === 6 || (r >= 2 && r <= 4 && c >= 2 && c <= 4))
      setModule(matrix, rr, cc, dark, true)
    }
  }
}

function drawAlignment(matrix, row, col) {
  for (let r = -2; r <= 2; r++) {
    for (let c = -2; c <= 2; c++) {
      const dark = Math.max(Math.abs(r), Math.abs(c)) !== 1
      setModule(matrix, row + r, col + c, dark, true)
    }
  }
}

function drawFunctionPatterns(matrix, version) {
  const size = matrix.modules.length
  drawFinder(matrix, 0, 0)
  drawFinder(matrix, 0, size - 7)
  drawFinder(matrix, size - 7, 0)

  for (let i = 8; i < size - 8; i++) {
    const dark = i % 2 === 0
    setModule(matrix, 6, i, dark, true)
    setModule(matrix, i, 6, dark, true)
  }

  const positions = ALIGNMENT_POSITIONS[version]
  for (const row of positions) {
    for (const col of positions) {
      if (matrix.reserved[row][col]) continue
      drawAlignment(matrix, row, col)
    }
  }

  setModule(matrix, size - 8, 8, true, true)
  reserveFormatAreas(matrix)
  if (version >= 7) drawVersionInfo(matrix, version)
}

function reserveFormatAreas(matrix) {
  const size = matrix.modules.length
  for (let i = 0; i < 9; i++) {
    if (i !== 6) {
      matrix.reserved[8][i] = true
      matrix.reserved[i][8] = true
    }
  }
  for (let i = 0; i < 8; i++) {
    matrix.reserved[8][size - 1 - i] = true
    matrix.reserved[size - 1 - i][8] = true
  }
}

function bchRemainder(value, generator) {
  let shift = bitLength(value) - bitLength(generator)
  while (shift >= 0) {
    value ^= generator << shift
    shift = bitLength(value) - bitLength(generator)
  }
  return value
}

function bitLength(value) {
  let length = 0
  while (value !== 0) {
    length++
    value >>>= 1
  }
  return length
}

function drawFormatInfo(matrix, mask) {
  const size = matrix.modules.length
  const data = (EC_LEVEL_L << 3) | mask
  const bits = ((data << 10) | bchRemainder(data << 10, 0x537)) ^ 0x5412

  for (let i = 0; i < 15; i++) {
    const dark = ((bits >>> i) & 1) !== 0
    const a = FORMAT_COORDS_1[i]
    const b = FORMAT_COORDS_2(size)[i]
    setModule(matrix, a[0], a[1], dark, true)
    setModule(matrix, b[0], b[1], dark, true)
  }
}

const FORMAT_COORDS_1 = [
  [8, 0], [8, 1], [8, 2], [8, 3], [8, 4], [8, 5], [8, 7], [8, 8],
  [7, 8], [5, 8], [4, 8], [3, 8], [2, 8], [1, 8], [0, 8],
]

function FORMAT_COORDS_2(size) {
  return [
    [size - 1, 8], [size - 2, 8], [size - 3, 8], [size - 4, 8], [size - 5, 8], [size - 6, 8], [size - 7, 8],
    [8, size - 8], [8, size - 7], [8, size - 6], [8, size - 5], [8, size - 4], [8, size - 3], [8, size - 2], [8, size - 1],
  ]
}

function drawVersionInfo(matrix, version) {
  const size = matrix.modules.length
  const bits = (version << 12) | bchRemainder(version << 12, 0x1f25)
  for (let i = 0; i < 18; i++) {
    const dark = ((bits >>> i) & 1) !== 0
    const row = Math.floor(i / 3)
    const col = i % 3
    setModule(matrix, row, size - 11 + col, dark, true)
    setModule(matrix, size - 11 + col, row, dark, true)
  }
}

function placeData(matrix, codewords) {
  const size = matrix.modules.length
  const bits = []
  for (const codeword of codewords) appendBits(bits, codeword, 8)

  let bitIndex = 0
  let upward = true
  for (let col = size - 1; col > 0; col -= 2) {
    if (col === 6) col--
    for (let i = 0; i < size; i++) {
      const row = upward ? size - 1 - i : i
      for (let c = 0; c < 2; c++) {
        const cc = col - c
        if (matrix.reserved[row][cc]) continue
        setModule(matrix, row, cc, bits[bitIndex] === 1, false)
        bitIndex++
      }
    }
    upward = !upward
  }
}

function applyMask(matrix, mask) {
  const size = matrix.modules.length
  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      if (matrix.reserved[row][col]) continue
      if (maskCondition(mask, row, col)) {
        matrix.modules[row][col] = !matrix.modules[row][col]
      }
    }
  }
}

function maskCondition(mask, row, col) {
  switch (mask) {
    case 0: return (row + col) % 2 === 0
    case 1: return row % 2 === 0
    case 2: return col % 3 === 0
    case 3: return (row + col) % 3 === 0
    case 4: return (Math.floor(row / 2) + Math.floor(col / 3)) % 2 === 0
    case 5: return ((row * col) % 2) + ((row * col) % 3) === 0
    case 6: return (((row * col) % 2) + ((row * col) % 3)) % 2 === 0
    case 7: return (((row + col) % 2) + ((row * col) % 3)) % 2 === 0
    default: return false
  }
}

function cloneMatrix(matrix) {
  return {
    modules: matrix.modules.map((row) => row.slice()),
    reserved: matrix.reserved.map((row) => row.slice()),
  }
}

function penaltyScore(modules) {
  const size = modules.length
  let score = 0

  for (let row = 0; row < size; row++) {
    let runColor = modules[row][0]
    let runLength = 1
    for (let col = 1; col < size; col++) {
      if (modules[row][col] === runColor) {
        runLength++
      } else {
        if (runLength >= 5) score += 3 + (runLength - 5)
        runColor = modules[row][col]
        runLength = 1
      }
    }
    if (runLength >= 5) score += 3 + (runLength - 5)
  }

  for (let col = 0; col < size; col++) {
    let runColor = modules[0][col]
    let runLength = 1
    for (let row = 1; row < size; row++) {
      if (modules[row][col] === runColor) {
        runLength++
      } else {
        if (runLength >= 5) score += 3 + (runLength - 5)
        runColor = modules[row][col]
        runLength = 1
      }
    }
    if (runLength >= 5) score += 3 + (runLength - 5)
  }

  for (let row = 0; row < size - 1; row++) {
    for (let col = 0; col < size - 1; col++) {
      const color = modules[row][col]
      if (modules[row][col + 1] === color && modules[row + 1][col] === color && modules[row + 1][col + 1] === color) {
        score += 3
      }
    }
  }

  const pattern = [true, false, true, true, true, false, true, false, false, false, false]
  const reverse = pattern.slice().reverse()
  for (let row = 0; row < size; row++) {
    for (let col = 0; col <= size - 11; col++) {
      const slice = modules[row].slice(col, col + 11)
      if (matches(slice, pattern) || matches(slice, reverse)) score += 40
    }
  }
  for (let col = 0; col < size; col++) {
    for (let row = 0; row <= size - 11; row++) {
      const slice = []
      for (let i = 0; i < 11; i++) slice.push(modules[row + i][col])
      if (matches(slice, pattern) || matches(slice, reverse)) score += 40
    }
  }

  let dark = 0
  for (const row of modules) {
    for (const module of row) if (module) dark++
  }
  const percent = (dark * 100) / (size * size)
  score += Math.floor(Math.abs(percent - 50) / 5) * 10
  return score
}

function matches(values, pattern) {
  return values.every((value, index) => value === pattern[index])
}

function encodeSvgDataUrl(modules, quietZone = 4) {
  const size = modules.length
  const fullSize = size + quietZone * 2
  const paths = []
  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      if (modules[row][col]) paths.push(`M${col + quietZone} ${row + quietZone}h1v1h-1z`)
    }
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${fullSize} ${fullSize}" shape-rendering="crispEdges"><path fill="#fff" d="M0 0h${fullSize}v${fullSize}H0z"/><path fill="#2D3436" d="${paths.join('')}"/></svg>`
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

export function createQrSvgDataUrl(text) {
  const bytes = utf8Bytes(text)
  const version = chooseVersion(bytes.length)
  const size = 17 + version * 4
  const dataCodewords = createDataCodewords(bytes, version)
  const codewords = createCodewords(dataCodewords, version)
  const baseMatrix = makeMatrix(size)

  drawFunctionPatterns(baseMatrix, version)
  placeData(baseMatrix, codewords)

  let bestMatrix = null
  let bestScore = Infinity
  for (let mask = 0; mask < 8; mask++) {
    const candidate = cloneMatrix(baseMatrix)
    applyMask(candidate, mask)
    drawFormatInfo(candidate, mask)
    const score = penaltyScore(candidate.modules)
    if (score < bestScore) {
      bestScore = score
      bestMatrix = candidate
    }
  }

  return encodeSvgDataUrl(bestMatrix.modules)
}
