// src/components/InfoTooltip.jsx
import React, { useState } from 'react'
import PropTypes from 'prop-types'

export default function InfoTooltip({ text }) {
  const [open, setOpen] = useState(false)

  return (
    <span className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        className="text-gray-400 hover:text-gray-600 ml-1"
        aria-label="Info"
      >
        ℹ
      </button>
      {open && (
        <div
          className="absolute z-10 w-64 p-3 bg-white border rounded shadow-lg right-0 mt-2 text-sm text-gray-700"
          onMouseLeave={() => setOpen(false)}
        >
          {text}
        </div>
      )}
    </span>
  )
}

InfoTooltip.propTypes = {
  text: PropTypes.string.isRequired,
}
