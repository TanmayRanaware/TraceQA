from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..services.testgen import TestGenerator
from ..schemas import TestGenerationRequest, TestGenerationResponse
import openpyxl
from openpyxl.styles import Font, Alignment
import io
from typing import List, Dict, Any

router = APIRouter(prefix="/api/tests", tags=["test-generation"])

@router.post("/generate")
async def generate_tests(payload: TestGenerationRequest):
    try:
        test_generator = TestGenerator()
        result = await test_generator.generate_test_cases(
            journey=payload.journey,
            max_cases=payload.max_cases,
            context="",  # Context will be built from RAG search
            source_types=None,  # Use all source types
            model=payload.model,
            temperature=None  # Use default temperature
        )
        
        return {
            "journey": payload.journey,
            "tests": result.get("test_cases", []),
            "metadata": result.get("metadata", {}),
            "debug": {
                "status": result.get("status", "unknown"),
                "message": result.get("message", ""),
                "total_generated": result.get("total_generated", 0),
                "context_used": result.get("context_used", "")[:200] + "..." if result.get("context_used") else "",
                "documents_used": len(result.get("context_used", "").split("Document")) - 1 if result.get("context_used") else 0
            }
        }
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tests: {str(e)}")


@router.post("/export-excel")
async def export_tests_to_excel(tests: List[Dict[str, Any]]):
    """Export test cases to Excel format"""
    try:
        # Create workbook and worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Test Cases"
        
        # Define headers
        headers = [
            "Key", "Name", "Status", "Precondition Objective", "Folder",
            "Priority", "Component Labels", "Owner", "Estimated Time", 
            "Coverage", "Test Script"
        ]
        
        # Add headers with styling
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Add test case data
        for row_idx, test in enumerate(tests, 2):
            # Handle component_labels as string
            component_labels_str = ", ".join(test.get("component_labels", [])) if test.get("component_labels") else ""
            
            row_data = [
                test.get("key", test.get("test_id", "")),
                test.get("name", test.get("title", "")),
                test.get("status", "Draft"),
                test.get("precondition_objective", ""),
                test.get("folder", ""),
                test.get("priority", ""),
                component_labels_str,
                test.get("owner", ""),
                test.get("estimated_time", ""),
                test.get("coverage", ""),
                test.get("test_script", "")
            ]
            
            for col, value in enumerate(row_data, 1):
                ws.cell(row=row_idx, column=col, value=value)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=test_cases.xlsx"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export tests: {str(e)}")
