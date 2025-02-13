
async function changeLicenseKey(licenseId) {

    const response = await fetch(`/admin/licenses/${licenseId}/change-key`, {
        method: 'POST',
    });

    const data = await response.json();

    if (data.error) {
        Swal.fire({
            icon: 'error',
            title: 'Lỗi',
            text: data.error,
        });
        return;
    }

    const licenseKeyCell = document.getElementById(`license-key-${licenseId}`);
    if (licenseKeyCell) {
        licenseKeyCell.textContent = data.new_key.slice(0, 16) + '...';
    }

    Swal.fire({
        icon: 'success',
        title: 'Thành công!',
        text: 'Key đã được thay đổi thành công!',
        timer: 2000, // Tự động đóng sau 2 giây
        showConfirmButton: false
    });


}


async function changeStatus(licenseId) {
    try {
        const response = await fetch(`/admin/licenses/${licenseId}/change-status`, {
            method: 'POST',
        });

        const data = await response.json();

        if (data.error) {
            Swal.fire({
                icon: 'error',
                title: 'Lỗi',
                text: data.error,
            });
            return;
        }

        const statusCell = document.getElementById(`license-status-${licenseId}`);
        const newStatus = data.new_status;

        // Thay đổi nội dung trạng thái
        statusCell.innerHTML = `
            <span class="badge ${newStatus === 'Active' ? 'bg-success' : 'bg-warning'}">
                ${newStatus === 'Active' ? 'Hoạt Động' : 'Không Hoạt Động'}
            </span>
        `;

        // Thông báo thành công
        Swal.fire({
            icon: 'success',
            title: 'Thành công!',
            text: `Trạng thái đã được thay đổi thành công!`,
            timer: 2000, // Đóng tự động sau 2 giây
            showConfirmButton: true
        });

    } catch (error) {
        console.error('Lỗi khi thay đổi trạng thái:', error);
        Swal.fire({
            icon: 'error',
            title: 'Lỗi',
            text: 'Đã xảy ra lỗi khi thay đổi trạng thái!',
        });
    }
}



async function deleteKey(licenseId) {
    const response = await fetch(`/admin/licenses/${licenseId}/delete-key`, {
        method: 'POST',
    });

    const data = await response.json();
    if (data.error) {
        Swal.fire({
            icon: 'error',
            title: 'Lỗi',
            text: data.error,
        });
        return;
    }

    const row = document.getElementById(`license-row-${licenseId}`);
    if (row) {
        row.style.transition = 'opacity 0.5s ease';
        row.style.opacity = '0';

        setTimeout(() => {
            row.remove();
            Swal.fire({
                icon: 'success',
                title: 'Thành công',
                text: 'Key đã được xóa thành công!',
            });
        }, 500);
    }
}





function openHistoryModal(id) {
    const modal = document.getElementById(`history-modal-${id}`);
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeHistoryModal(id) {
    const modal = document.getElementById(`history-modal-${id}`);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Thêm sự kiện khi click ra ngoài modal để đóng modal
window.addEventListener('click', function (event) {
    const modal = event.target;
    if (modal.classList.contains('modal-overlay')) {
        // Kiểm tra nếu người dùng nhấn vào overlay và không phải vào content
        const modalId = modal.id.split('-')[2];
        closeHistoryModal(modalId); // Đóng modal
    }
});
